use crate::{
    db::models::RuntimeConfig,
    error::ErrorResponse,
    services::config_service::ConfigService,
};

#[tauri::command]
pub async fn get_runtime_config() -> Result<RuntimeConfig, ErrorResponse> {
    ConfigService::load().map_err(Into::into)
}
