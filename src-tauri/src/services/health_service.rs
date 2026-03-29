use chrono::Utc;
use tauri::State;

use crate::{
    db::{
        connection,
        models::{BackendStatus, DatabaseCheckResult},
        repositories::HealthRepository,
    },
    error::AppError,
    services::config_service::ConfigService,
    state::AppState,
};

pub struct HealthService;

impl HealthService {
    pub async fn backend_status(state: &AppState) -> Result<BackendStatus, AppError> {
        let config = ConfigService::load()?;
        let database_url = ConfigService::database_url().unwrap_or_default();
        let database_configured = !database_url.trim().is_empty();
        let database_connected = state.db_pool.read().await.is_some();

        Ok(BackendStatus {
            app_name: "Plano de Corte Backend".to_string(),
            app_env: config.app_env,
            database_configured,
            database_connected,
            machine_name: config.machine_name,
            checked_at: Utc::now(),
        })
    }

    pub async fn test_database_connection(
        state: &AppState,
    ) -> Result<DatabaseCheckResult, AppError> {
        let database_url = ConfigService::database_url()?;
        let pool = connection::create_pool(&database_url).await?;
        connection::ping_database(&pool).await?;
        let database_name = HealthRepository::database_name(&pool).await?;

        {
            let mut writer = state.db_pool.write().await;
            *writer = Some(pool);
        }

        Ok(DatabaseCheckResult {
            ok: true,
            message: format!("conexao com MariaDB OK (database: {database_name})"),
            checked_at: Utc::now(),
        })
    }
}
