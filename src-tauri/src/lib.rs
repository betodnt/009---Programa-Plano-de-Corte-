pub mod error;
pub mod state;
pub mod models;
pub mod commands;
pub mod db;
pub mod services;

use crate::state::AppState;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState::default())
        .setup(|app| {
            dotenvy::dotenv().ok();
            let handle = app.handle().clone();
            tauri::async_runtime::block_on(async move {
                if let Ok(url) = std::env::var("DATABASE_URL") {
                    if let Ok(pool) = sqlx::MySqlPool::connect(&url).await {
                        let state = handle.state::<AppState>();
                        let mut pool_guard = state.db_pool.write().await;
                        *pool_guard = Some(pool);
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::system::validate_system_paths,
            commands::config_commands::get_runtime_config,
            commands::health_commands::get_backend_status,
            commands::health_commands::test_database_connection,
            commands::operation_commands::bootstrap_database,
            commands::operation_commands::get_bootstrap_data,
            commands::operation_commands::start_operation,
            commands::operation_commands::finish_operation,
            commands::operation_commands::touch_operation_lock,
            commands::monitor_commands::get_monitor_snapshot,
            commands::file_commands::search_cnc_files,
            commands::file_commands::open_pdf,
        ])
        .run(tauri::generate_context!())
        .expect("erro ao iniciar aplicação tauri");
}