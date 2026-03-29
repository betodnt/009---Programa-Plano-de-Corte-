use std::env;

use crate::{
    db::models::RuntimeConfig,
    error::AppError,
};

pub struct ConfigService;

impl ConfigService {
    pub fn load() -> Result<RuntimeConfig, AppError> {
        let app_env = env::var("APP_ENV").unwrap_or_else(|_| "development".to_string());
        let machine_name = env::var("MACHINE_NAME").unwrap_or_else(|_| "Bodor1 (12K)".to_string());
        let database_url = env::var("DATABASE_URL").unwrap_or_default();

        Ok(RuntimeConfig {
            app_env,
            machine_name,
            database_url_masked: mask_database_url(&database_url),
        })
    }

    pub fn database_url() -> Result<String, AppError> {
        env::var("DATABASE_URL").map_err(|_| {
            AppError::Config("defina a variavel de ambiente DATABASE_URL".to_string())
        })
    }

    pub fn lock_timeout_seconds() -> i64 {
        env::var("LOCK_TIMEOUT_SECONDS")
            .ok()
            .and_then(|value| value.parse::<i64>().ok())
            .filter(|value| *value > 0)
            .unwrap_or(14_400)
    }

    pub fn server_path() -> Result<String, AppError> {
        env::var("SERVER_PATH").map_err(|_| {
            AppError::Config("defina a variavel SERVER_PATH (ex: K:\\)".to_string())
        })
    }

    pub fn saidas_cnc_path() -> Result<String, AppError> {
        env::var("SAIDAS_CNC_PATH").map_err(|_| {
            AppError::Config("defina a variavel SAIDAS_CNC_PATH (ex: C:\\Saidas_CNC)".to_string())
        })
    }

    pub fn saidas_cortadas_path() -> Result<String, AppError> {
        env::var("SAIDAS_CORTADAS_PATH").map_err(|_| {
            AppError::Config("defina a variavel SAIDAS_CORTADAS_PATH (ex: C:\\Saidas_Cortadas)".to_string())
        })
    }
}

fn mask_database_url(value: &str) -> String {
    if value.trim().is_empty() {
        return String::new();
    }

    match value.split_once("://") {
        Some((scheme, rest)) => {
            if let Some((_, host_part)) = rest.split_once('@') {
                format!("{scheme}://****@{host_part}")
            } else {
                format!("{scheme}://{rest}")
            }
        }
        None => value.to_string(),
    }
}
