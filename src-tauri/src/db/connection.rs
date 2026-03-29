use sqlx::{mysql::MySqlPoolOptions, MySqlPool};
use std::time::Duration;

use crate::{error::AppError, state::AppState};

pub async fn create_pool(database_url: &str) -> Result<MySqlPool, AppError> {
    if database_url.trim().is_empty() {
        return Err(AppError::Config(
            "DATABASE_URL nao foi definido".to_string(),
        ));
    }

    let pool = MySqlPoolOptions::new()
        .max_connections(10)
        .min_connections(1)
        .acquire_timeout(Duration::from_secs(5))
        .connect(database_url)
        .await?;

    Ok(pool)
}

pub async fn ping_database(pool: &MySqlPool) -> Result<(), AppError> {
    sqlx::query("SELECT 1").execute(pool).await?;
    Ok(())
}

pub async fn get_or_create_pool(state: &AppState, database_url: &str) -> Result<MySqlPool, AppError> {
    {
        let reader = state.db_pool.read().await;
        if let Some(pool) = reader.as_ref() {
            return Ok(pool.clone());
        }
    }

    let pool = create_pool(database_url).await?;

    {
        let mut writer = state.db_pool.write().await;
        *writer = Some(pool.clone());
    }

    Ok(pool)
}
