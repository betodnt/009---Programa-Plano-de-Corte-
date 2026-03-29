use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeConfig {
    pub app_env: String,
    pub machine_name: String,
    pub database_url_masked: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BackendStatus {
    pub app_name: String,
    pub app_env: String,
    pub database_configured: bool,
    pub database_connected: bool,
    pub machine_name: String,
    pub checked_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize)]
pub struct DatabaseCheckResult {
    pub ok: bool,
    pub message: String,
    pub checked_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize)]
pub struct MachineSummary {
    pub id: i64,
    pub name: String,
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct OperatorSummary {
    pub id: i64,
    pub name: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct OperationSummary {
    pub operation_id: String,
    pub pedido: String,
    pub operator_name: String,
    pub machine_name: String,
    pub saida: String,
    pub tipo: Option<String>,
    pub status: String,
    pub started_at: DateTime<Utc>,
    pub finished_at: Option<DateTime<Utc>>,
    pub elapsed_seconds: Option<i32>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ActiveLockSummary {
    pub machine_name: String,
    pub saida: String,
    pub operator_name: String,
    pub operation_id: String,
    pub heartbeat_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize)]
pub struct MonitorSnapshot {
    pub active_operations: Vec<OperationSummary>,
    pub active_locks: Vec<ActiveLockSummary>,
    pub machines: Vec<MachineSummary>,
    pub generated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize)]
pub struct BootstrapData {
    pub runtime: RuntimeConfig,
    pub machines: Vec<MachineSummary>,
    pub operators: Vec<OperatorSummary>,
    pub generated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct StartOperationInput {
    pub pedido: String,
    pub operador: String,
    pub maquina: String,
    pub retalho: Option<String>,
    pub saida: String,
    pub tipo: Option<String>,
    pub owner_id: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct StartOperationResult {
    pub operation_id: String,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct FinishOperationInput {
    pub operation_id: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct FinishOperationResult {
    pub operation_id: String,
    pub status: String,
    pub elapsed_seconds: i32,
    pub message: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BootstrapResult {
    pub ok: bool,
    pub message: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LockHeartbeatInput {
    pub operation_id: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct LockHeartbeatResult {
    pub ok: bool,
    pub message: String,
    pub heartbeat_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SearchCncInput {
    pub pedido: String,
    pub tipo: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct SearchCncResult {
    pub files: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct OpenPdfInput {
    pub cnc_filename: String,
}
