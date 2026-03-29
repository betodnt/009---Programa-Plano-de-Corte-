use tauri::State;
use chrono::Utc;

use crate::{
    db::{
        connection,
        models::{
            BootstrapData, BootstrapResult, FinishOperationInput, FinishOperationResult,
            LockHeartbeatInput, LockHeartbeatResult, StartOperationInput, StartOperationResult,
        },
        repositories::{
            LockRepository, MachineRepository, OperationRepository, OperatorRepository,
            SettingsRepository,
        },
    },
    error::AppError,
    services::{
        config_service::ConfigService,
        file_service::FileService,
    },
    state::AppState,
};
use std::path::Path;

pub struct OperationService;

impl OperationService {
    pub async fn bootstrap_database(state: &AppState) -> Result<BootstrapResult, AppError> {
        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let schema = include_str!("../../database/schema.sql");

        for statement in schema.split(';') {
            let sql = statement.trim();
            if sql.is_empty() {
                continue;
            }
            sqlx::query(sql).execute(&pool).await?;
        }

        let config = ConfigService::load()?;
        SettingsRepository::set(&pool, "machine", "default_machine_name", &config.machine_name).await?;
        let mut connection = pool.acquire().await?;
        MachineRepository::ensure_machine(&mut connection, &config.machine_name).await?;

        Ok(BootstrapResult {
            ok: true,
            message: "schema inicial aplicado com sucesso".to_string(),
        })
    }

    pub async fn start_operation(
        state: &AppState,
        input: StartOperationInput,
    ) -> Result<StartOperationResult, AppError> {
        validate_start_input(&input)?;

        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let mut connection = pool.acquire().await?;
        LockRepository::cleanup_expired(&mut connection, ConfigService::lock_timeout_seconds()).await?;

        let operator_id = OperatorRepository::ensure_operator(&mut connection, input.operador.trim()).await?;
        let machine_id = MachineRepository::ensure_machine(&mut connection, input.maquina.trim()).await?;
        let owner_id = input
            .owner_id
            .clone()
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| format!("desktop:{}", input.maquina.trim()));

        let (operation_id, _) = OperationRepository::insert_started(
            &mut connection,
            input.pedido.trim(),
            operator_id,
            machine_id,
            input.retalho.as_deref(),
            input.saida.trim(),
            input.tipo.as_deref(),
        )
        .await?;

        LockRepository::acquire(
            &mut connection,
            machine_id,
            input.saida.trim(),
            &operation_id,
            operator_id,
            &owner_id,
        )
        .await?;

        let server_path = ConfigService::server_path()?;
        let local_path = ConfigService::saidas_cnc_path()?;
        
        let src_file = Path::new(&server_path).join(input.saida.trim());
        let dst_file = Path::new(&local_path).join(input.saida.trim());

        FileService::copy_file(&src_file, &dst_file)?;

        Ok(StartOperationResult {
            operation_id,
            status: "started".to_string(),
            message: "operacao iniciada com sucesso".to_string(),
        })
    }

    pub async fn finish_operation(
        state: &AppState,
        input: FinishOperationInput,
    ) -> Result<FinishOperationResult, AppError> {
        if input.operation_id.trim().is_empty() {
            return Err(AppError::Config("operation_id e obrigatorio".to_string()));
        }

        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let mut connection = pool.acquire().await?;
        LockRepository::cleanup_expired(&mut connection, ConfigService::lock_timeout_seconds()).await?;

        let (operation_id, elapsed_seconds, saida) =
            OperationRepository::finish(&mut connection, input.operation_id.trim()).await?;
        LockRepository::release_by_operation(&mut connection, &operation_id).await?;

        let local_path = ConfigService::saidas_cnc_path()?;
        let cortadas_path = ConfigService::saidas_cortadas_path()?;

        let src_file = Path::new(&local_path).join(&saida);
        let dst_file = Path::new(&cortadas_path).join(&saida);

        FileService::move_file(&src_file, &dst_file)?;

        Ok(FinishOperationResult {
            operation_id,
            status: "finished".to_string(),
            elapsed_seconds,
            message: "operacao finalizada com sucesso".to_string(),
        })
    }

    pub async fn touch_lock(
        state: &AppState,
        input: LockHeartbeatInput,
    ) -> Result<LockHeartbeatResult, AppError> {
        if input.operation_id.trim().is_empty() {
            return Err(AppError::Config("operation_id e obrigatorio".to_string()));
        }

        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let mut connection = pool.acquire().await?;
        LockRepository::cleanup_expired(&mut connection, ConfigService::lock_timeout_seconds()).await?;
        let touched = LockRepository::touch_by_operation(&mut connection, input.operation_id.trim()).await?;

        Ok(LockHeartbeatResult {
            ok: touched,
            message: if touched {
                "heartbeat atualizado".to_string()
            } else {
                "lock nao encontrado para esta operacao".to_string()
            },
            heartbeat_at: Utc::now(),
        })
    }

    pub async fn get_bootstrap_data(state: &AppState) -> Result<BootstrapData, AppError> {
        let database_url = ConfigService::database_url()?;
        let pool = connection::get_or_create_pool(state, &database_url).await?;
        let runtime = ConfigService::load()?;
        let machines = MachineRepository::list_active(&pool).await?;
        let operators = OperatorRepository::list_recent(&pool, 20).await?;

        Ok(BootstrapData {
            runtime,
            machines,
            operators,
            generated_at: Utc::now(),
        })
    }
}

fn validate_start_input(input: &StartOperationInput) -> Result<(), AppError> {
    if input.pedido.trim().is_empty() {
        return Err(AppError::Config("pedido e obrigatorio".to_string()));
    }
    if input.operador.trim().is_empty() {
        return Err(AppError::Config("operador e obrigatorio".to_string()));
    }
    if input.maquina.trim().is_empty() {
        return Err(AppError::Config("maquina e obrigatoria".to_string()));
    }
    if input.saida.trim().is_empty() {
        return Err(AppError::Config("saida e obrigatoria".to_string()));
    }
    Ok(())
}
