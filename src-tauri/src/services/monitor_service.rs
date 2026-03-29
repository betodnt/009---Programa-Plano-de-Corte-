use chrono::Utc;
use tauri::State;

use crate::{
    db::{
        connection,
        models::MonitorSnapshot,
        repositories::{LockRepository, MachineRepository, OperationRepository},
    },
    error::AppError,
    services::config_service::ConfigService,
    state::AppState,
};

pub struct MonitorService;

impl MonitorService {
    pub async fn get_snapshot(state: &AppState) -> Result<MonitorSnapshot, AppError> {
        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let mut connection = pool.acquire().await?;
        LockRepository::cleanup_expired(&mut connection, ConfigService::lock_timeout_seconds()).await?;

        let active_operations = OperationRepository::list_active(&pool).await?;
        let active_locks = LockRepository::list_active(&pool).await?;
        let machines = MachineRepository::list_active(&pool).await?;

        Ok(MonitorSnapshot {
            active_operations,
            active_locks,
            machines,
            generated_at: Utc::now(),
        })
    }
}
