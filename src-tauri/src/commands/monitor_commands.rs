use tauri::State;

use crate::{
    db::models::MonitorSnapshot,
    error::ErrorResponse,
    services::monitor_service::MonitorService,
    state::AppState,
};

#[tauri::command]
pub async fn get_monitor_snapshot(
    state: State<'_, AppState>,
) -> Result<MonitorSnapshot, ErrorResponse> {
    MonitorService::get_snapshot(state.inner())
        .await
        .map_err(Into::into)
}
