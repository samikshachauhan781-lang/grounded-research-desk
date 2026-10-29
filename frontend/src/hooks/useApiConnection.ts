import { useEffect, useState } from "react";
import { resolveApiBase } from "../lib/api/client";

export type ConnectionState = "connecting" | "connected" | "disconnected";

export function useApiConnection(): ConnectionState {
  const [state, setState] = useState<ConnectionState>("connecting");

  useEffect(() => {
    let cancelled = false;
    async function ping() {
      const base = await resolveApiBase();
      if (!cancelled) setState(base !== null ? "connected" : "disconnected");
    }
    void ping();
    const id = window.setInterval(ping, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return state;
}
