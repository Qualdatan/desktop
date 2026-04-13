// SPDX-License-Identifier: AGPL-3.0-only
//! Sidecar-Lifecycle.
//!
//! Startet den Python-Sidecar entweder als externe Tauri-Binary
//! (`binaries/qualdatan-sidecar`, via PyInstaller bereitgestellt) oder —
//! im Dev-Modus — als `python -m qualdatan_sidecar` ueber `PATH`.
//! Parst die Handshake-Zeile auf stdout und legt den Child-Prozess-Handle
//! fuer einen sauberen Shutdown ab.

use anyhow::{anyhow, Context, Result};
use serde::Deserialize;
use std::process::Stdio;
use tauri::AppHandle;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};
use tokio::time::{timeout, Duration};

/// Handshake-Payload, den der Sidecar auf stdout druckt.
#[derive(Debug, Clone, Deserialize)]
pub struct SidecarHandshake {
    pub port: u16,
    pub token: String,
}

/// Laufender Sidecar-Prozess + Handshake.
pub struct SidecarHandle {
    pub handshake: SidecarHandshake,
    child: Option<Child>,
}

impl SidecarHandle {
    /// Beendet den Sidecar synchron (best effort).
    pub fn shutdown(mut self) {
        if let Some(mut child) = self.child.take() {
            // Best effort — wir warten nicht auf Graceful-Exit, Sidecar hat
            // keinen IPC-Kanal fuer Shutdown.
            let _ = child.start_kill();
        }
    }
}

/// Startet den Sidecar und wartet bis zu 15s auf die Handshake-Zeile.
pub async fn spawn_sidecar(_app: &AppHandle) -> Result<SidecarHandle> {
    let mut cmd = build_command();
    cmd.stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);

    let mut child = cmd.spawn().context("failed to spawn sidecar")?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| anyhow!("sidecar stdout not captured"))?;

    let mut reader = BufReader::new(stdout).lines();

    let handshake = timeout(Duration::from_secs(15), async {
        while let Some(line) = reader.next_line().await? {
            let trimmed = line.trim();
            if trimmed.is_empty() || !trimmed.starts_with('{') {
                tracing::debug!(%trimmed, "sidecar preamble");
                continue;
            }
            match serde_json::from_str::<SidecarHandshake>(trimmed) {
                Ok(hs) => return Ok::<_, anyhow::Error>(hs),
                Err(err) => {
                    tracing::warn!(?err, %trimmed, "handshake parse failed");
                }
            }
        }
        Err(anyhow!("sidecar closed stdout without handshake"))
    })
    .await
    .context("timeout waiting for sidecar handshake")??;

    // stdout weiter leeren, damit der Pipe-Buffer nicht vollaeuft.
    tauri::async_runtime::spawn(async move {
        while let Ok(Some(line)) = reader.next_line().await {
            tracing::debug!(target: "sidecar::stdout", %line);
        }
    });

    Ok(SidecarHandle {
        handshake,
        child: Some(child),
    })
}

/// Baut das passende Command-Objekt.
///
/// - Im Release-Bundle liegt der Sidecar als `binaries/qualdatan-sidecar`
///   neben der Hauptbinary (Tauri kopiert `externalBin`).
/// - Im Dev-Modus nehmen wir `python -m qualdatan_sidecar` via PATH.
fn build_command() -> Command {
    if let Ok(path) = std::env::current_exe() {
        if let Some(parent) = path.parent() {
            let candidate = parent.join(if cfg!(windows) {
                "qualdatan-sidecar.exe"
            } else {
                "qualdatan-sidecar"
            });
            if candidate.exists() {
                tracing::info!(?candidate, "using bundled sidecar");
                return Command::new(candidate);
            }
        }
    }

    tracing::info!("falling back to 'python -m qualdatan_sidecar'");
    let mut cmd = Command::new(if cfg!(windows) { "python" } else { "python3" });
    cmd.arg("-m").arg("qualdatan_sidecar");
    cmd
}
