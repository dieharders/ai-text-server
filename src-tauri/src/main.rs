// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::api::process::Command;
use tauri::api::process::CommandEvent;

fn start_backend() {
  // `new_sidecar()` expects just the filename, NOT the whole path
  let (mut rx, mut child) = Command::new_sidecar("main")
  .expect("failed to create `main.exe` binary command")
  .spawn()
  .expect("Failed to spawn sidecar");

  tauri::async_runtime::spawn(async move {
    // read events such as stdout
    while let Some(event) = rx.recv().await {
      if let CommandEvent::Stdout(line) = event {
        // write to stdin
        child.write("message from Rust\n".as_bytes()).unwrap();
        // @TODO How to shutdown process when tauri app is closed?
      }
    }
  });
}

fn main() {
  tauri::Builder::default()
      .setup(|app| {
        start_backend();
        Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
