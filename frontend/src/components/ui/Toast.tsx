import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

type ToastContextValue = { notify: (message: string) => void };

const ToastContext = createContext<ToastContextValue>({ notify: () => undefined });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Array<{ id: number; text: string }>>([]);

  const notify = useCallback((text: string) => {
    const id = Date.now() + Math.random();
    setMessages((m) => [...m, { id, text }]);
    window.setTimeout(() => setMessages((m) => m.filter((x) => x.id !== id)), 2800);
  }, []);

  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="grd-toast-stack" aria-live="polite">
        {messages.map((m) => (
          <div key={m.id} className="grd-toast" role="status">
            {m.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
