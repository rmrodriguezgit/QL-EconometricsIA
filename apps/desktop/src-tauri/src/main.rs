#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::Value;
use std::{io::{Read, Write}, path::PathBuf, process::{Command, Stdio}, sync::mpsc, time::Duration};

fn call_engine(request: Value) -> Result<Value, String> {
    let encoded = serde_json::to_vec(&request).map_err(|_| "Solicitud no válida")?;
    if encoded.len() > 4_000_000 { return Err("Proyecto demasiado grande".into()); }
    let mut command;
    if cfg!(debug_assertions) {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
        let python = if cfg!(windows) { root.join(".venv/Scripts/python.exe") } else { root.join(".venv/bin/python") };
        command = Command::new(python);
        command.args(["-m", "quantlabs"]).current_dir(&root)
            .env("PYTHONPATH", root.join("engine"))
            .env("WBDATA_CACHE_PATH", root.join(".cache/wbdata/cache"))
            .env("PYTHONUTF8", "1");
    } else {
        let executable = std::env::current_exe().map_err(|_| "Ruta de aplicación no disponible")?;
        let name = if cfg!(windows) { "quantlabs-engine.exe" } else { "quantlabs-engine" };
        command = Command::new(executable.parent().ok_or("Directorio no disponible")?.join(name));
    }
    let mut child = command.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::inherit())
        .spawn().map_err(|_| "No se pudo iniciar Python. Ejecuta uv sync antes de iniciar el modo de desarrollo.")?;
    let mut input = child.stdin.take().ok_or("Entrada no disponible")?;
    if input.write_all(&encoded).and_then(|_| input.write_all(b"\n")).is_err() {
        let _ = child.kill(); let _ = child.wait(); return Err("No se pudo enviar el proyecto".into());
    }
    drop(input);
    let output = child.stdout.take().ok_or("Salida no disponible")?;
    let (sender, receiver) = mpsc::channel();
    std::thread::spawn(move || {
        let mut bytes = Vec::new();
        let result = output.take(12_000_001).read_to_end(&mut bytes).map(|_| bytes);
        let _ = sender.send(result);
    });
    let received = receiver.recv_timeout(Duration::from_secs(60));
    let value = match received {
        Ok(Ok(bytes)) if bytes.len() <= 12_000_000 => serde_json::from_slice::<Value>(&bytes).map_err(|_| "Respuesta inválida del motor".to_string()),
        Ok(_) => Err("El motor excedió el límite de salida o se interrumpió".into()),
        Err(_) => Err("El motor superó 60 segundos".into()),
    };
    let _ = child.kill();
    let _ = child.wait();
    value
}

#[tauri::command]
async fn engine_request(request: Value) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || call_engine(request)).await
        .map_err(|_| "No se pudo completar la ejecución".to_string())?
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![engine_request])
        .run(tauri::generate_context!())
        .expect("No se pudo iniciar Quantlabs");
}
