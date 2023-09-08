// @TODO This is not preventing terminal window from opening on release builds.
// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]
// #![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
// #![windows_subsystem = "windows"]

// @TODO May be able to nest these in their respective funcs
use command_group::CommandGroup;
use std::process::Command;
use std::sync::mpsc::{sync_channel, Receiver};
use std::thread;
use tauri::api::process::Command as TCommand;
use tauri::Manager;
use tauri::WindowEvent;

mod model;
mod utils;

fn start_backend(receiver: Receiver<i32>) {
    // `new_sidecar()` expects just the filename, NOT the whole path
    let t =
        TCommand::new_sidecar("main").expect("[Error] Failed to create `main.exe` binary command");
    let mut group = Command::from(t)
        .group_spawn()
        .expect("[Error] spawning api server process.");
    thread::spawn(move || loop {
        let s = receiver.recv();
        if s.unwrap() == -1 {
            group.kill().expect("[Error] killing api server process.");
        }
    });
}

fn main() {
    // Startup the python binary (api service)
    let (tx, rx) = sync_channel(1);
    start_backend(rx);

    tauri::Builder::default()
        // https://github.com/tauri-apps/plugins-workspace/tree/v1/plugins/persisted-scope
        .plugin(tauri_plugin_persisted_scope::init())
        .setup(|app| {
            // Show debug window on startup.
            // Only include this code on debug builds.
            #[cfg(debug_assertions)]
            {
                let window = app.get_window("main").unwrap();
                window.open_devtools();
                window.close_devtools();
            }

            // config::State::new(app)?; // is this is needed ?
            // model::config::State::new(app)?; // is this is needed ?
            model::downloader::State::new(app)?;
            model::integrity::State::new(app)?;
            Ok(())
        })
        // Custom Command handlers
        .invoke_handler(tauri::generate_handler![
            model::directory::delete_model_file,
            model::downloader::get_download_progress,
            model::downloader::start_download,
            model::downloader::pause_download,
            model::downloader::resume_download,
            // model::integrity::compute_model_integrity, // is this is needed ?
            // model::integrity::get_cached_integrity, // is this is needed ?
            // model::config::get_model_config, // is this is needed ?
            // model::config::set_model_config, // is this is needed ?
        ])
        // Tell the child process to shutdown when app exits
        .on_window_event(move |event| match event.event() {
            WindowEvent::Destroyed => {
                tx.send(-1).expect("[Error] sending msg.");
                println!("[Event] App closed, shutting down API...");
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("[Error] while running tauri application");
}
