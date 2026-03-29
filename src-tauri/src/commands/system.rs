use crate::error::{AppError, ErrorResponse};
use crate::models::PathStatus;
use serde::Serialize;
use std::fs;

#[derive(Serialize)]
pub struct RuntimeConfig {
    pub machine_name: String,
    pub app_env: String,
    pub database_url_masked: String,
}

#[tauri::command]
pub async fn health_check() -> Result<String, String> {
    Ok("Sistema operacional".to_string())
}



#[tauri::command]
pub async fn validate_system_paths() -> Result<Vec<PathStatus>, ErrorResponse> {
    let paths = vec![
        ("Entrada CNC", ".\\Public\\saidas_cnc"),
        ("Dados XML", ".\\Public\\dados"),
        ("Logs", ".\\Public\\logs"),
    ];

    Ok(paths.into_iter().map(|(label, path)| {
        let meta = fs::metadata(path);
        PathStatus {
            label: label.into(),
            path: path.into(),
            exists: meta.is_ok(),
            is_dir: meta.map(|m| m.is_dir()).unwrap_or(false),
        }
    }).collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_health_check_returns_ok() {
        let result = health_check().await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "Sistema operacional");
    }

    #[tokio::test]
    async fn test_runtime_config_has_production_env() {
        // Mock env var se necessário
        std::env::set_var("PCP_MACHINE_ID", "Test-Machine");
        let config = get_runtime_config().await.unwrap();
        assert_eq!(config.machine_name, "Test-Machine");
        assert_eq!(config.app_env, "production");
    }
}