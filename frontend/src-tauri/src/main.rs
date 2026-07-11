#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use reqwest::Client;

const BACKEND_URL: &str = "http://127.0.0.1:4321";

mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::start_workspace,
            commands::stop_workspace,
            commands::get_status,
            commands::new_identity,
            commands::purge_all,
            commands::open_browser_window,
        ])
        .setup(|app| {
            app.manage(Client::new());
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
