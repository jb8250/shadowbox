use serde::{Deserialize, Serialize};
use tauri::{State, AppHandle};

#[derive(Debug, Serialize, Deserialize)]
pub struct StartRequest {
    pub workspace: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StopRequest {
    pub workspace: String,
    pub keep_downloads: bool,
}

#[tauri::command]
pub async fn start_workspace(
    client: State<'_, reqwest::Client>,
    workspace: String,
) -> Result<serde_json::Value, String> {
    let body = StartRequest { workspace };
    client
        .post(format!("{}/start", crate::BACKEND_URL))
        .json(&body)
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn stop_workspace(
    client: State<'_, reqwest::Client>,
    workspace: String,
    keep_downloads: bool,
) -> Result<serde_json::Value, String> {
    let body = StopRequest {
        workspace,
        keep_downloads,
    };
    client
        .post(format!("{}/stop", crate::BACKEND_URL))
        .json(&body)
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json()
        .await
        .map_err(|e| e.to_string())
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StatusResponse {
    pub workspace: String,
    pub status: String,
    pub identity: Option<String>,
    pub storage_bytes: u64,
}

#[tauri::command]
pub async fn get_status(
    client: State<'_, reqwest::Client>,
    workspace: String,
) -> Result<StatusResponse, String> {
    let resp = client
        .get(format!("{}/status", crate::BACKEND_URL))
        .query(&[("workspace", workspace)])
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json::<StatusResponse>()
        .await
        .map_err(|e| e.to_string())?;
    Ok(resp)
}

#[tauri::command]
pub async fn new_identity(
    client: State<'_, reqwest::Client>,
    workspace: String,
) -> Result<serde_json::Value, String> {
    #[derive(Serialize)]
    struct Body {
        workspace: String,
    }
    client
        .post(format!("{}/identity/new", crate::BACKEND_URL))
        .json(&Body { workspace })
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn purge_all(client: State<'_, reqwest::Client>) -> Result<serde_json::Value, String> {
    client
        .post(format!("{}/purge", crate::BACKEND_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json()
        .await
        .map_err(|e| e.to_string())
}

fn open(url: &str) -> std::io::Result<()> {
    let _ = std::process::Command::new("open").arg(url).status();
    Ok(())
}

#[tauri::command]
pub async fn open_browser_window(_app: AppHandle) -> Result<(), String> {
    let url = "https://localhost:3001";
    open(url).map_err(|e| e.to_string())?;
    Ok(())
}
