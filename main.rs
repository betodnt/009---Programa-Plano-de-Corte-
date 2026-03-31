use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use chrono::Local;
use ini::Ini;
use tauri::Manager;

#[derive(Serialize, Deserialize, Clone)]
pub struct RuntimeConfig {
    pub machine_name: String,
    pub paths: std::collections::HashMap<String, String>,
}

#[derive(Serialize, Deserialize)]
pub struct OperationInput {
    pub pedido: String,
    pub operador: String,
    pub maquina: String,
    pub retalho: String,
    pub saida: String,
    pub tipo: String,
}

#[derive(Serialize, Deserialize)]
pub struct StartOperationResult {
    pub operation_id: String,
    pub ok: bool,
}

#[derive(Serialize, Deserialize)]
pub struct SearchResult {
    pub files: Vec<String>,
}

// Função auxiliar para ler o config.ini e garantir que as pastas existam
fn get_config() -> (String, String, String, String) {
    let config_path = "config.ini";
    let conf = Ini::load_from_file(config_path).unwrap_or_else(|_| {
        let mut new_conf = Ini::new();
        new_conf.with_section(Some("Machine"))
            .set("machine_name", "Bodor1 (12K)");
        new_conf.with_section(Some("Paths"))
            .set("SaidasCnc", "./Public/saidas_cnc")
            .set("LocksFile", "./Public/app_data/active_locks.json")
            .set("DadosXml", "./Public/dados/dados_{date}.xml");
        new_conf.write_to_file(config_path).unwrap();
        new_conf
    });

    let machine = conf.get_from(Some("Machine"), "machine_name").unwrap_or("Bodor1 (12K)").to_string();
    
    // Busca o caminho das saídas, tentando as chaves comuns no seu config.ini
    let saidas_path = conf.get_from(Some("Paths"), "SaidasCnc")
        .or_else(|| conf.get_from(Some("Paths"), "AcervoSaidasCNC"))
        .unwrap_or("./Public/saidas_cnc")
        .to_string();

    let xml_path = conf.get_from(Some("Paths"), "DadosXml")
        .unwrap_or("./Public/dados/dados_{date}.xml")
        .to_string();

    let locks_path = conf.get_from(Some("Paths"), "LocksFile")
        .unwrap_or("./Public/app_data/active_locks.json")
        .to_string();

    // CRIAÇÃO AUTOMÁTICA DE PASTAS: Garante que os diretórios pai existam
    for path_str in &[&saidas_path, &xml_path, &locks_path] {
        if let Some(parent) = Path::new(path_str).parent() {
            let _ = fs::create_dir_all(parent);
        }
    }

    let machine_id = std::env::var("PCP_MACHINE_ID").unwrap_or(machine);
    (machine_id, saidas_path, xml_path, locks_path)
}

#[tauri::command]
async fn get_runtime_config() -> Result<RuntimeConfig, String> {
    let (machine, _, _, _) = get_config();
    Ok(RuntimeConfig {
        machine_name: machine,
        paths: std::collections::HashMap::new(),
    })
}

#[tauri::command]
async fn search_cnc_files(pedido: String, tipo: String) -> Result<SearchResult, String> {
    let (_, saidas_path, _, _) = get_config();
    let mut files = Vec::new();
    
    // Simula a busca no diretório configurado
    if let Ok(entries) = fs::read_dir(saidas_path) {
        for entry in entries.flatten() { 
            let name = entry.file_name().to_string_lossy().to_string();
            if name.contains(&pedido) {
                files.push(name);
            }
        }
    }
    Ok(SearchResult { files })
}

#[tauri::command]
async fn start_operation(input: OperationInput) -> Result<StartOperationResult, String> {
    let (_, _, _, lock_file) = get_config();
    let op_id = format!("{}_{}", input.pedido, Local::now().format("%H%M%S"));
    
    // Lógica de Lock
    let mut locks: Vec<serde_json::Value> = if let Ok(data) = fs::read_to_string(&lock_file) {
        serde_json::from_str(&data).unwrap_or_default()
    } else {
        Vec::new()
    };

    locks.push(serde_json::json!({
        "operation_id": op_id,
        "pedido": input.pedido,
        "saida": input.saida,
        "operador": input.operador,
        "maquina": input.maquina,
        "started_at": Local::now().to_rfc3339()
    }));

    fs::write(&lock_file, serde_json::to_string_pretty(&locks).unwrap()).map_err(|e| e.to_string())?;

    Ok(StartOperationResult { operation_id: op_id, ok: true })
}

#[tauri::command]
async fn open_pdf(cnc_filename: String) -> Result<(), String> {
    // No Windows, abre o arquivo com o visualizador padrão
    let path = format!("./Public/saidas_cnc/{}.pdf", cnc_filename.to_lowercase().replace(".cnc", ""));
    if cfg!(target_os = "windows") {
        Command::new("cmd").args(["/C", "start", "", &path]).spawn().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn get_monitor_snapshot(date: String) -> Result<serde_json::Value, String> {
    let (_, _, xml_template, lock_file) = get_config();
    
    let active_operations: serde_json::Value = if let Ok(data) = fs::read_to_string(&lock_file) {
        serde_json::from_str(&data).unwrap_or(serde_json::json!([]))
    } else {
        serde_json::json!([])
    };

    // Resolve o caminho do XML para a data fornecida (ex: 30/03/2026 -> 30_03_2026)
    let safe_date = date.replace("/", "_");
    let current_xml_path = xml_template.replace("{date}", &safe_date);
    
    // CRIAÇÃO AUTOMÁTICA DO XML: Se não existir o arquivo do dia, cria um vazio com a tag raiz
    if !Path::new(&current_xml_path).exists() {
        let initial_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<history>\n</history>";
        let _ = fs::write(&current_xml_path, initial_xml);
    }

    let mut history_items = Vec::new();
    if let Ok(xml_content) = fs::read_to_string(&current_xml_path) {
        // Parsing simples do XML, compatível com o formato legado do histórico
        let mut reader = quick_xml::Reader::from_str(&xml_content);
        let mut buf = Vec::new();
        loop {
            match reader.read_event_into(&mut buf) {
                Ok(quick_xml::events::Event::Empty(ref e)) if e.name().as_ref() == b"operation" => {
                    let mut item = serde_json::Map::new();
                    for attr in e.attributes().flatten() {
                        let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                        let value = String::from_utf8_lossy(&attr.value).to_string();
                        item.insert(key, serde_json::Value::String(value));
                    }
                    history_items.push(serde_json::Value::Object(item));
                }
                Ok(quick_xml::events::Event::Eof) => break,
                Err(_) => break,
                _ => {}
            }
            buf.clear();
        }
    }

    // Inverte o histórico para mostrar os mais recentes primeiro
    history_items.reverse();

    Ok(serde_json::json!({
        "active_operations": active_operations,
        "active_locks": active_operations,
        "history_items": history_items,
        "history_total": history_items.len()
    }))
}

#[tauri::command]
async fn finish_operation(operation_id: String) -> Result<serde_json::Value, String> {
    let (machine_id, _, xml_template, lock_file) = get_config();
    let mut locks: Vec<serde_json::Value> = if let Ok(data) = fs::read_to_string(&lock_file) {
        serde_json::from_str(&data).unwrap_or_default()
    } else {
        return Err("Arquivo de travas não encontrado".into());
    };

    let index = locks.iter().position(|l| l["operation_id"] == operation_id);
    
    if let Some(i) = index {
        let removed = locks.remove(i);
        fs::write(&lock_file, serde_json::to_string_pretty(&locks).unwrap())
            .map_err(|e| e.to_string())?;
        
        // Calcular duração e salvar no XML no mesmo formato histórico
        let start_str = removed["started_at"].as_str().unwrap_or("");
        let start_dt = chrono::DateTime::parse_from_rfc3339(start_str).map(|d| d.with_timezone(&Local)).ok();
        let now = Local::now();
        
        let duration_str = if let Some(st) = start_dt {
            let diff = now.signed_duration_since(st);
            format!("{:02}:{:02}:{:02}", diff.num_hours(), diff.num_minutes() % 60, diff.num_seconds() % 60)
        } else {
            "00:00:00".to_string()
        };

        let safe_date = now.format("%d_%m_%Y").to_string();
        let current_xml_path = xml_template.replace("{date}", &safe_date);
        
        let mut xml_content = fs::read_to_string(&current_xml_path).unwrap_or_else(|_| {
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<history>\n</history>".to_string()
        });

        let new_entry = format!(
            "  <operation operador=\"{}\" maquina=\"{}\" pedido=\"{}\" saida=\"{}\" duracao=\"{}\" hora_fim=\"{}\" />\n",
            removed["operador"].as_str().unwrap_or(""),
            removed["maquina"].as_str().unwrap_or(&machine_id),
            removed["pedido"].as_str().unwrap_or(""),
            removed["saida"].as_str().unwrap_or(""),
            duration_str,
            now.format("%H:%M:%S")
        );

        if let Some(pos) = xml_content.find("</history>") {
            xml_content.insert_str(pos, &new_entry);
            let _ = fs::write(&current_xml_path, xml_content);
        }

        Ok(serde_json::json!({ 
            "ok": true, 
            "elapsed_seconds": 0,
            "duration": duration_str
        }))
    } else {
        Err("Operação ativa não encontrada para finalização.".into())
    }
}

#[tauri::command]
async fn open_monitor_window(handle: tauri::AppHandle) -> Result<(), String> {
    // Busca se a janela já existe para dar foco em vez de abrir outra
    if let Some(window) = handle.get_webview_window("monitor") {
        window.set_focus().map_err(|e| e.to_string())?;
    } else {
        tauri::WebviewWindowBuilder::new(
            &handle,
            "monitor",
            tauri::WebviewUrl::App("index.html?view=monitor".into()),
        )
        .title("Monitor de Operações - Tempo Real")
        .inner_size(820.0, 500.0)
        .resizable(true)
        .build()
        .map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_runtime_config,
            search_cnc_files,
            start_operation,
            open_pdf,
            get_monitor_snapshot,
            open_monitor_window,
            finish_operation
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}