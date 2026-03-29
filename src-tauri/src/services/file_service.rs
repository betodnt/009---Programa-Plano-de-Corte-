use std::fs;
use std::path::{Path, PathBuf};

use crate::error::AppError;

pub struct FileService;

impl FileService {
    fn get_prefix_for_tipo(tipo: &str) -> Option<&'static str> {
        match tipo {
            "Pedido" => Some("P"),
            "Avulso" => Some("A"),
            "Estoque" => Some("E"),
            "PPD" => Some("PPD"),
            "Reforma" => Some("R"),
            _ => None,
        }
    }

    pub fn find_matching_saidas(
        pedido: &str,
        tipo: &str,
        base_path: &Path,
    ) -> Result<Vec<String>, AppError> {
        let prefix = match Self::get_prefix_for_tipo(tipo) {
            Some(p) => p,
            None => return Ok(vec![]),
        };

        if !base_path.exists() {
            return Err(AppError::Config(format!(
                "O diretorio base nao existe: {:?}",
                base_path
            )));
        }

        let mut results = Vec::new();
        let entries = fs::read_dir(base_path)
            .map_err(|e| AppError::Io(format!("Erro lendo diretorio {:?}: {}", base_path, e)))?;

        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                if let Some(filename) = path.file_name().and_then(|n| n.to_str()) {
                    if filename.to_lowercase().ends_with(".cnc") {
                        let parts: Vec<&str> = filename.split('_').collect();
                        for part in parts {
                            if part.starts_with(prefix) && &part[prefix.len()..] == pedido {
                                results.push(filename.to_string());
                                break;
                            }
                        }
                    }
                }
            }
        }

        results.sort();
        Ok(results)
    }

    pub fn find_pdf(pdf_filename: &str, start_path: &Path) -> Result<Option<String>, AppError> {
        if !start_path.exists() {
            return Ok(None);
        }

        // Simple BFS for directories
        let mut dirs_to_visit = vec![start_path.to_path_buf()];

        while let Some(current_dir) = dirs_to_visit.pop() {
            let entries = match fs::read_dir(&current_dir) {
                Ok(e) => e,
                Err(_) => continue, // Ignore permissions errors and unreadable dirs
            };

            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    dirs_to_visit.push(path);
                } else if path.is_file() {
                    if let Some(filename) = path.file_name().and_then(|n| n.to_str()) {
                        if filename == pdf_filename {
                            return Ok(Some(path.to_string_lossy().to_string()));
                        }
                    }
                }
            }
        }

        Ok(None)
    }

    pub fn copy_file(src: &Path, dst: &Path) -> Result<(), AppError> {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)
                .map_err(|e| AppError::Io(format!("Erro ao criar diretorio pai: {}", e)))?;
        }
        
        fs::copy(src, dst)
            .map_err(|e| AppError::Io(format!("Erro copiando {:?} para {:?}: {}", src, dst, e)))?;
            
        Ok(())
    }

    pub fn move_file(src: &Path, dst: &Path) -> Result<(), AppError> {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)
                .map_err(|e| AppError::Io(format!("Erro ao criar diretorio pai: {}", e)))?;
        }
        
        fs::rename(src, dst)
            .or_else(|_| {
                // Se rename falhar por cruzamento de file systems
                fs::copy(src, dst)?;
                fs::remove_file(src)?;
                Ok::<_, std::io::Error>(())
            })
            .map_err(|e| AppError::Io(format!("Erro movendo {:?} para {:?}: {}", src, dst, e)))?;
            
        Ok(())
    }
}
