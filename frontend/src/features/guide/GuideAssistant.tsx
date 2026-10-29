import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/icons/Icon";
import { GUIDE_ASSISTANT_NAME, GUIDE_ENABLED } from "./guideConfig";
import {
  matchGuideQuery,
  WELCOME_REPLY,
  SUGGESTED_CHIPS,
  type GuideLink,
  type GuideReply,
} from "./guideEngine";

type ChatLine = { role: "user" | "assistant"; text: string; links?: GuideLink[] };

function replyToLine(reply: GuideReply): ChatLine {
  return { role: "assistant", text: reply.text, links: reply.links };
}

export function GuideAssistant() {
  const navigate = useNavigate();
  const titleId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatLine[]>(() => [replyToLine(WELCOME_REPLY)]);
  const [chips, setChips] = useState<string[]>(SUGGESTED_CHIPS);

  const resetConversation = useCallback(() => {
    setMessages([replyToLine(WELCOME_REPLY)]);
    setChips(SUGGESTED_CHIPS);
    setInput("");
  }, []);

  const sendUserMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const reply = matchGuideQuery(trimmed);
    setMessages((m) => [...m, { role: "user", text: trimmed }, replyToLine(reply)]);
    if (reply.followUpChips?.length) setChips(reply.followUpChips);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    inputRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  function navigateTo(to: string) {
    navigate(to);
    setOpen(false);
  }

  if (!GUIDE_ENABLED) return null;

  return (
    <>
      {!open ? (
        <button
          type="button"
          className="grd-guide-fab"
          aria-label="Open Research Desk Guide"
          onClick={() => setOpen(true)}
        >
          <Icon name="bot" size={22} />
        </button>
      ) : null}
      {open ? (
        <div className="grd-guide-root" role="presentation">
          <button type="button" className="grd-guide-backdrop" aria-label="Close guide" onClick={() => setOpen(false)} />
          <div
            ref={panelRef}
            className="grd-guide-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
          >
            <header className="grd-guide-header">
              <div>
                <h2 id={titleId} className="grd-guide-title">
                  {GUIDE_ASSISTANT_NAME}
                </h2>
                <p className="grd-guide-subtitle">Built-in FAQ · not a live AI chatbot</p>
              </div>
              <div className="grd-guide-header-actions">
                <button type="button" className="grd-btn grd-btn-ghost grd-icon-btn" aria-label="Restart conversation" onClick={resetConversation}>
                  ↺
                </button>
                <button type="button" className="grd-btn grd-btn-ghost grd-icon-btn" aria-label="Close guide" onClick={() => setOpen(false)}>
                  <Icon name="close" />
                </button>
              </div>
            </header>
            <div className="grd-guide-messages" aria-live="polite">
              {messages.map((msg, i) => (
                <div key={i} className={`grd-guide-bubble ${msg.role}`}>
                  <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{msg.text}</p>
                  {msg.links?.length ? (
                    <div className="grd-guide-links">
                      {msg.links.map((link) => (
                        <button key={link.to + link.label} type="button" className="grd-chip" onClick={() => navigateTo(link.to)}>
                          {link.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
            <div className="grd-guide-chips">
              {chips.map((c) => (
                <button key={c} type="button" className="grd-chip" onClick={() => sendUserMessage(c)}>
                  {c.length > 42 ? `${c.slice(0, 42)}…` : c}
                </button>
              ))}
            </div>
            <form
              className="grd-guide-form"
              onSubmit={(e) => {
                e.preventDefault();
                sendUserMessage(input);
                setInput("");
              }}
            >
              <label className="grd-sr-only" htmlFor="guide-input">
                Ask the guide
              </label>
              <input
                id="guide-input"
                ref={inputRef}
                className="grd-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask how to use the app…"
                autoComplete="off"
              />
              <button type="submit" className="grd-btn grd-btn-primary" disabled={!input.trim()}>
                Send
              </button>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
