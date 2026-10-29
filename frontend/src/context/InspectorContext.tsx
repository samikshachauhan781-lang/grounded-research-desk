import { createContext, useContext, useState, type ReactNode } from "react";
import type { Citation } from "../lib/api/client";

type InspectorState = {
  citation: Citation | null;
  documentId: string | null;
  setCitation: (c: Citation | null) => void;
  openDocument: (id: string) => void;
  clear: () => void;
};

const InspectorContext = createContext<InspectorState | null>(null);

export function InspectorProvider({ children }: { children: ReactNode }) {
  const [citation, setCitation] = useState<Citation | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);

  return (
    <InspectorContext.Provider
      value={{
        citation,
        documentId,
        setCitation: (c) => {
          setCitation(c);
          if (c) setDocumentId(c.document_id);
        },
        openDocument: (id) => {
          setDocumentId(id);
          setCitation(null);
        },
        clear: () => {
          setCitation(null);
          setDocumentId(null);
        },
      }}
    >
      {children}
    </InspectorContext.Provider>
  );
}

export function useInspector() {
  const ctx = useContext(InspectorContext);
  if (!ctx) throw new Error("useInspector requires InspectorProvider");
  return ctx;
}
