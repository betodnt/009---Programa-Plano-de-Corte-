use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("configuracao invalida: {0}")]
    Config(String),
    #[error("erro de banco de dados: {0}")]
    Database(String),
    #[error("erro interno: {0}")]
    Internal(String),
    #[error("erro de leitura de arquivo: {0}")]
    Io(String),
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub message: String,
}

impl From<AppError> for ErrorResponse {
    fn from(value: AppError) -> Self {
        Self {
            message: value.to_string(),
        }
    }
}

impl From<sqlx::Error> for AppError {
    fn from(value: sqlx::Error) -> Self {
        Self::Database(value.to_string())
    }
}

impl From<anyhow::Error> for AppError {
    fn from(value: anyhow::Error) -> Self {
        Self::Internal(value.to_string())
    }
}

impl From<std::io::Error> for AppError {
    fn from(value: std::io::Error) -> Self {
        Self::Io(value.to_string())
    }
}
