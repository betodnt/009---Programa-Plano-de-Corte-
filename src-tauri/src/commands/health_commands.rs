use tauri::State;

use crate::{
    db::models::{BackendStatus, DatabaseCheckResult},
    error::ErrorResponse,
    services::health_service::HealthService,
    state::AppState,
};

#[tauri::command]
pub async fn get_backend_status(
    state: State<'_, AppState>,
) -> Result<BackendStatus, ErrorResponse> {
    HealthService::backend_status(state.inner())
        .await
        .map_err(Into::into)
}

#[tauri::command]
pub async fn test_database_connection(
    state: State<'_, AppState>,
) -> Result<DatabaseCheckResult, ErrorResponse> {
    HealthService::test_database_connection(state.inner())
        .await
        .map_err(Into::into)
}
