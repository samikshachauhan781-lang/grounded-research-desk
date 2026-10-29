import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../lib/api/client";
import { EmptyState } from "../../components/ui/EmptyState";
import { Prose } from "../../components/ui/Prose";

type Message = {
  message_id: string;
  question: string;
  answer: string;
  citations: Array<{ filename: string; snippet: string }>;
  created_at: string;
};

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [title, setTitle] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    Promise.all([api.getSession(sessionId), api.getSessionMessages(sessionId)])
      .then(([session, msgs]) => {
        setTitle(session.title);
        setMessages(msgs);
      })
      .catch(() => setError("Session not found or unavailable."));
  }, [sessionId]);

  if (!sessionId) return null;

  return (
    <div className="grd-page">
      <p className="grd-meta">
        <Link to="/history">History</Link>
        <span className="grd-crumb"> / {title || "Session"}</span>
      </p>
      <h1 style={{ margin: "0.75rem 0 1.5rem", fontSize: "var(--grd-text-xl)", letterSpacing: "-0.03em" }}>
        {title || "Research session"}
      </h1>
      {error ? <div className="grd-alert warning">{error}</div> : null}
      {messages.length === 0 && !error ? (
        <EmptyState title="No messages" body="This session has no saved Q&A yet." />
      ) : null}
      {messages.map((m) => (
        <article key={m.message_id} style={{ padding: "1.25rem 0", borderBottom: "1px solid var(--grd-border-subtle)" }}>
          <p className="grd-meta">{m.created_at}</p>
          <p style={{ fontWeight: 600, margin: "0.5rem 0" }}>{m.question}</p>
          <Prose text={m.answer} />
          {m.citations.length ? (
            <ul style={{ margin: "0.75rem 0 0", paddingLeft: "1.25rem", fontSize: "var(--grd-text-sm)" }}>
              {m.citations.map((c, i) => (
                <li key={i}>
                  {c.filename}: {c.snippet.slice(0, 120)}
                  {c.snippet.length > 120 ? "…" : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </div>
  );
}
