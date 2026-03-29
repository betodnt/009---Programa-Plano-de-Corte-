use sqlx::MySqlPool;
use tokio::sync::RwLock;

#[derive(Default)]
pub struct AppState {
    pub db_pool: RwLock<Option<MySqlPool>>,
}
