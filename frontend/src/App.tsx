import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

type Status = {
  workspace: string;
  status: string;
  identity?: string;
  storage_bytes: number;
};

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [workspace, setWorkspace] = useState("default");

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [workspace]);

  async function refresh() {
    try {
      const s: Status = await invoke("get_status", { workspace });
      setStatus(s);
    } catch (err) {
      console.error(err);
    }
  }

  async function start() {
    await invoke("start_workspace", { workspace });
    await refresh();
  }

  async function stop() {
    await invoke("stop_workspace", { workspace, keep_downloads: true });
    await refresh();
  }

  async function rotate() {
    await invoke("new_identity", { workspace });
    await refresh();
  }

  async function purge() {
    if (!confirm("Emergency purge: destroy all data now?")) return;
    await invoke("purge_all");
    await refresh();
  }

  return (
    <div className="panel">
      <h1>ShadowBox</h1>
      <div className="row">
        <label>
          Workspace:{" "}
          <input
            value={workspace}
            onChange={(e) => setWorkspace(e.target.value)}
          />
        </label>
      </div>
      <div className="row">
        Tor: {status?.status === "running" ? "Connected" : "Disconnected"}
      </div>
      <div className="row">
        Identity: {status?.identity ?? "—"}
      </div>
      <div className="row">
        Storage: {status?.storage_bytes ?? 0} bytes
      </div>
      <div className="actions">
        <button onClick={start}>Open Browser</button>
        <button onClick={stop}>Stop</button>
        <button onClick={rotate}>New Identity</button>
        <button onClick={purge}>Emergency Purge</button>
      </div>
    </div>
  );
}
