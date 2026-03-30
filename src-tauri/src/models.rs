use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct CncFile {
    pub name: String,
    pub path: String,
    pub last_modified: String,
    pub size_bytes: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OperationUpdate {
    pub file_name: String,
    pub machine_id: String,
    pub operator: String,
    pub status: String,
}

#[derive(Debug, Serialize)]
pub struct PathStatus {
    pub label: String,
    pub path: String,
    pub exists: bool,
    pub is_dir: bool,
}