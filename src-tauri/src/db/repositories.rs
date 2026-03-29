use chrono::{DateTime, NaiveDateTime, Utc};
use sqlx::{pool::PoolConnection, MySql, MySqlPool};
use uuid::Uuid;

use crate::{
    db::models::{
        ActiveLockSummary, MachineSummary, OperationSummary, OperatorSummary,
    },
    error::AppError,
};

pub struct HealthRepository;
pub struct MachineRepository;
pub struct OperatorRepository;
pub struct OperationRepository;
pub struct LockRepository;
pub struct SettingsRepository;

impl HealthRepository {
    pub async fn database_name(pool: &MySqlPool) -> Result<String, AppError> {
        let row: (Option<String>,) = sqlx::query_as("SELECT DATABASE()")
            .fetch_one(pool)
            .await?;

        Ok(row.0.unwrap_or_else(|| "sem_database()".to_string()))
    }
}

impl MachineRepository {
    pub async fn ensure_machine(connection: &mut PoolConnection<MySql>, name: &str) -> Result<i64, AppError> {
        sqlx::query(
            "INSERT INTO machines (name, is_active)
             VALUES (?, 1)
             ON DUPLICATE KEY UPDATE is_active = VALUES(is_active)",
        )
        .bind(name)
        .execute(&mut **connection)
        .await?;

        let row: (i64,) = sqlx::query_as("SELECT id FROM machines WHERE name = ?")
            .bind(name)
            .fetch_one(&mut **connection)
            .await?;

        Ok(row.0)
    }

    pub async fn list_active(pool: &MySqlPool) -> Result<Vec<MachineSummary>, AppError> {
        let rows = sqlx::query_as::<_, (i64, String, i8)>(
            "SELECT id, name, is_active
             FROM machines
             WHERE is_active = 1
             ORDER BY name",
        )
        .fetch_all(pool)
        .await?;

        Ok(rows
            .into_iter()
            .map(|(id, name, is_active)| MachineSummary {
                id,
                name,
                is_active: is_active != 0,
            })
            .collect())
    }
}

impl OperatorRepository {
    pub async fn ensure_operator(connection: &mut PoolConnection<MySql>, name: &str) -> Result<i64, AppError> {
        sqlx::query(
            "INSERT INTO operators (name)
             VALUES (?)
             ON DUPLICATE KEY UPDATE name = VALUES(name)",
        )
        .bind(name)
        .execute(&mut **connection)
        .await?;

        let row: (i64,) = sqlx::query_as("SELECT id FROM operators WHERE name = ?")
            .bind(name)
            .fetch_one(&mut **connection)
            .await?;

        Ok(row.0)
    }

    pub async fn list_recent(pool: &MySqlPool, limit: i64) -> Result<Vec<OperatorSummary>, AppError> {
        let rows = sqlx::query_as::<_, (i64, String)>(
            "SELECT id, name
             FROM operators
             ORDER BY created_at DESC, name ASC
             LIMIT ?",
        )
        .bind(limit)
        .fetch_all(pool)
        .await?;

        Ok(rows
            .into_iter()
            .map(|(id, name)| OperatorSummary { id, name })
            .collect())
    }
}

impl OperationRepository {
    pub async fn insert_started(
        connection: &mut PoolConnection<MySql>,
        pedido: &str,
        operator_id: i64,
        machine_id: i64,
        retalho: Option<&str>,
        saida: &str,
        tipo: Option<&str>,
    ) -> Result<(String, DateTime<Utc>), AppError> {
        let operation_id = Uuid::new_v4().simple().to_string();
        let started_at = Utc::now();
        let started_at_db = started_at.naive_utc();

        sqlx::query(
            "INSERT INTO operations
             (operation_id, pedido, operator_id, machine_id, retalho, saida, tipo, started_at, status)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'started')",
        )
        .bind(&operation_id)
        .bind(pedido)
        .bind(operator_id)
        .bind(machine_id)
        .bind(retalho)
        .bind(saida)
        .bind(tipo)
        .bind(started_at_db)
        .execute(&mut **connection)
        .await?;

        Ok((operation_id, started_at))
    }

    pub async fn finish(
        connection: &mut PoolConnection<MySql>,
        operation_id: &str,
    ) -> Result<(String, i32, String), AppError> {
        let row: (String, NaiveDateTime, Option<NaiveDateTime>, String, String) = sqlx::query_as(
            "SELECT operation_id, started_at, finished_at, status, saida
             FROM operations
             WHERE operation_id = ?",
        )
        .bind(operation_id)
        .fetch_one(&mut **connection)
        .await?;

        if row.2.is_some() || row.3 == "finished" {
            let elapsed = row
                .2
                .map(|finished_at| (finished_at - row.1).num_seconds() as i32)
                .unwrap_or(0);
            return Ok((row.0, elapsed, row.4));
        }

        let finished_at = Utc::now();
        let started_at = DateTime::<Utc>::from_naive_utc_and_offset(row.1, Utc);
        let elapsed_seconds = (finished_at - started_at).num_seconds().max(0) as i32;

        sqlx::query(
            "UPDATE operations
             SET finished_at = ?, elapsed_seconds = ?, status = 'finished'
             WHERE operation_id = ?",
        )
        .bind(finished_at.naive_utc())
        .bind(elapsed_seconds)
        .bind(operation_id)
        .execute(&mut **connection)
        .await?;

        Ok((operation_id.to_string(), elapsed_seconds, row.4))
    }

    pub async fn list_active(pool: &MySqlPool) -> Result<Vec<OperationSummary>, AppError> {
        let rows = sqlx::query_as::<_, (String, String, String, String, String, Option<String>, String, NaiveDateTime, Option<NaiveDateTime>, Option<i32>)>(
            "SELECT
                o.operation_id,
                o.pedido,
                op.name,
                m.name,
                o.saida,
                o.tipo,
                o.status,
                o.started_at,
                o.finished_at,
                o.elapsed_seconds
             FROM operations o
             INNER JOIN operators op ON op.id = o.operator_id
             INNER JOIN machines m ON m.id = o.machine_id
             WHERE o.status = 'started'
             ORDER BY o.started_at DESC",
        )
        .fetch_all(pool)
        .await?;

        Ok(rows
            .into_iter()
            .map(
                |(operation_id, pedido, operator_name, machine_name, saida, tipo, status, started_at, finished_at, elapsed_seconds)| {
                    OperationSummary {
                        operation_id,
                        pedido,
                        operator_name,
                        machine_name,
                        saida,
                        tipo,
                        status,
                        started_at: DateTime::<Utc>::from_naive_utc_and_offset(started_at, Utc),
                        finished_at: finished_at
                            .map(|value| DateTime::<Utc>::from_naive_utc_and_offset(value, Utc)),
                        elapsed_seconds,
                    }
                },
            )
            .collect())
    }
}

impl LockRepository {
    pub async fn cleanup_expired(
        connection: &mut PoolConnection<MySql>,
        timeout_seconds: i64,
    ) -> Result<u64, AppError> {
        let threshold = Utc::now() - chrono::Duration::seconds(timeout_seconds);
        let result = sqlx::query("DELETE FROM machine_locks WHERE heartbeat_at < ?")
            .bind(threshold.naive_utc())
            .execute(&mut **connection)
            .await?;

        Ok(result.rows_affected())
    }

    pub async fn acquire(
        connection: &mut PoolConnection<MySql>,
        machine_id: i64,
        saida: &str,
        operation_id: &str,
        operator_id: i64,
        owner_id: &str,
    ) -> Result<(), AppError> {
        sqlx::query(
            "INSERT INTO machine_locks
             (machine_id, saida, operation_id, operator_id, owner_id, heartbeat_at)
             VALUES (?, ?, ?, ?, ?, ?)",
        )
        .bind(machine_id)
        .bind(saida)
        .bind(operation_id)
        .bind(operator_id)
        .bind(owner_id)
        .bind(Utc::now().naive_utc())
        .execute(&mut **connection)
        .await
        .map_err(|error| match &error {
            sqlx::Error::Database(db_error) if db_error.message().contains("Duplicate entry") => {
                AppError::Config("esta saida ja esta em uso por outro operador".to_string())
            }
            _ => AppError::from(error),
        })?;

        Ok(())
    }

    pub async fn touch_by_operation(
        connection: &mut PoolConnection<MySql>,
        operation_id: &str,
    ) -> Result<bool, AppError> {
        let result = sqlx::query(
            "UPDATE machine_locks
             SET heartbeat_at = ?
             WHERE operation_id = ?",
        )
        .bind(Utc::now().naive_utc())
        .bind(operation_id)
        .execute(&mut **connection)
        .await?;

        Ok(result.rows_affected() > 0)
    }

    pub async fn release_by_operation(
        connection: &mut PoolConnection<MySql>,
        operation_id: &str,
    ) -> Result<(), AppError> {
        sqlx::query("DELETE FROM machine_locks WHERE operation_id = ?")
            .bind(operation_id)
            .execute(&mut **connection)
            .await?;
        Ok(())
    }

    pub async fn list_active(pool: &MySqlPool) -> Result<Vec<ActiveLockSummary>, AppError> {
        let rows = sqlx::query_as::<_, (String, String, String, String, NaiveDateTime)>(
            "SELECT m.name, l.saida, op.name, l.operation_id, l.heartbeat_at
             FROM machine_locks l
             INNER JOIN machines m ON m.id = l.machine_id
             INNER JOIN operators op ON op.id = l.operator_id
             ORDER BY l.created_at DESC",
        )
        .fetch_all(pool)
        .await?;

        Ok(rows
            .into_iter()
            .map(
                |(machine_name, saida, operator_name, operation_id, heartbeat_at)| ActiveLockSummary {
                    machine_name,
                    saida,
                    operator_name,
                    operation_id,
                    heartbeat_at: DateTime::<Utc>::from_naive_utc_and_offset(heartbeat_at, Utc),
                },
            )
            .collect())
    }
}

impl SettingsRepository {
    pub async fn set(pool: &MySqlPool, scope: &str, key: &str, value: &str) -> Result<(), AppError> {
        sqlx::query(
            "INSERT INTO settings (scope, `key`, `value`)
             VALUES (?, ?, ?)
             ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)",
        )
        .bind(scope)
        .bind(key)
        .bind(value)
        .execute(pool)
        .await?;

        Ok(())
    }
}
