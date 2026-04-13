// SPDX-License-Identifier: AGPL-3.0-only
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! Tauri-Shell fuer Qualdatan Desktop.
//!
//! Startet beim Anwendungsstart den Python-Sidecar (`qualdatan-sidecar`) als
//! Kind-Prozess, liest die Handshake-Zeile (`{"port": u16, "token": String}`)
//! von dessen stdout und legt Port + Token in den Tauri-State. Frontend
//! greift via `get_sidecar_port` / `get_sidecar_token` darauf zu und
//! injiziert den Token als `X-Sidecar-Token`-Header.

mod sidecar;

use parking_lot::Mutex;
use std::sync::Arc;
use tauri::{Manager, RunEvent};

use sidecar::{SidecarHandle, SidecarHandshake};

/// Shared-State fuer den laufenden Sidecar.
#[derive(Default)]
struct AppState {
    sidecar: Mutex<Option<SidecarHandle>>,
}

/// Liefert den Port des laufenden Sidecars.
#[tauri::command]
fn get_sidecar_port(state: tauri::State<'_, Arc<AppState>>) -> Result<u16, String> {
    state
        .sidecar
        .lock()
        .as_ref()
        .map(|h| h.handshake.port)
        .ok_or_else(|| "sidecar not started".to_string())
}

/// Liefert den Auth-Token des laufenden Sidecars.
#[tauri::command]
fn get_sidecar_token(state: tauri::State<'_, Arc<AppState>>) -> Result<String, String> {
    state
        .sidecar
        .lock()
        .as_ref()
        .map(|h| h.handshake.token.clone())
        .ok_or_else(|| "sidecar not started".to_string())
}

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    let state = Arc::new(AppState::default());
    let state_setup = state.clone();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(state.clone())
        .invoke_handler(tauri::generate_handler![get_sidecar_port, get_sidecar_token])
        .setup(move |app| {
            let handle = app.handle().clone();
            let state = state_setup.clone();
            tauri::async_runtime::spawn(async move {
                match sidecar::spawn_sidecar(&handle).await {
                    Ok(h) => {
                        tracing::info!(
                            port = h.handshake.port,
                            "sidecar up"
                        );
                        *state.sidecar.lock() = Some(h);
                    }
                    Err(err) => {
                        tracing::error!(?err, "sidecar spawn failed");
                    }
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build tauri app");

    app.run(move |_app_handle, event| {
        if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
            if let Some(handle) = state.sidecar.lock().take() {
                handle.shutdown();
            }
        }
    });
}

// Re-export fuer Integrationstests.
#[allow(dead_code)]
pub(crate) use sidecar::SidecarHandshake as _SidecarHandshake;
