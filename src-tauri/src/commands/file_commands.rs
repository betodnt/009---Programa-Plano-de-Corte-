use std::path::Path;

use crate::{
    db::models::{OpenPdfInput, SearchCncInput, SearchCncResult},
    error::{AppError, ErrorResponse},
    services::{config_service::ConfigService, file_service::FileService},
};

#[tauri::command]
pub async fn search_cnc_files(input: SearchCncInput) -> Result<SearchCncResult, ErrorResponse> {
    let server_path_str = ConfigService::server_path().map_err(AppError::from)?;
    let base_path = Path::new(&server_path_str);

    let files = FileService::find_matching_saidas(&input.pedido, &input.tipo, base_path)?;
        
    Ok(SearchCncResult { files })
}

#[tauri::command]
pub async fn open_pdf(input: OpenPdfInput) -> Result<bool, ErrorResponse> {
    let server_path_str = ConfigService::server_path().map_err(AppError::from)?;
    let base_path = Path::new(&server_path_str);

    let pdf_filename = input.cnc_filename.replace(".cnc", ".pdf");

    if let Some(path) = FileService::find_pdf(&pdf_filename, base_path)? {
        std::process::Command::new("cmd")
            .args(&["/C", "start", "", &path])
            .spawn()
            .map_err(|e| AppError::Io(e.to_string()))?;
        Ok(true)
    } else {
        Err(AppError::Internal("PDF nao encontrado".to_string()).into())
    }
}
