use tauri::State;

use crate::{
    db::models::{
        BootstrapData, BootstrapResult, FinishOperationInput, FinishOperationResult,
        LockHeartbeatInput, LockHeartbeatResult, StartOperationInput, StartOperationResult,
    },
    error::ErrorResponse,
    services::operation_service::OperationService,
    state::AppState,
};

#[tauri::command]
pub async fn bootstrap_database(
    state: State<'_, AppState>,
) -> Result<BootstrapResult, ErrorResponse> {
    OperationService::bootstrap_database(state.inner())
        .await
        .map_err(Into::into)
}

#[tauri::command]
pub async fn start_operation(
    state: State<'_, AppState>,
    input: StartOperationInput,
) -> Result<StartOperationResult, ErrorResponse> {
    OperationService::start_operation(state.inner(), input)
        .await
        .map_err(Into::into)
}

#[tauri::command]
pub async fn finish_operation(
    state: State<'_, AppState>,
    input: FinishOperationInput,
) -> Result<FinishOperationResult, ErrorResponse> {
    OperationService::finish_operation(state.inner(), input)
        .await
        .map_err(Into::into)
}

#[tauri::command]
pub async fn touch_operation_lock(
    state: State<'_, AppState>,
    input: LockHeartbeatInput,
) -> Result<LockHeartbeatResult, ErrorResponse> {
    OperationService::touch_lock(state.inner(), input)
        .await
        .map_err(Into::into)
}

#[tauri::command]
pub async fn get_bootstrap_data(
    state: State<'_, AppState>,
) -> Result<BootstrapData, ErrorResponse> {
    OperationService::get_bootstrap_data(state.inner())
        .await
        .map_err(Into::into)
}
