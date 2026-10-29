import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useApiConnection } from "../hooks/useApiConnection";
import { MobileNavDrawer } from "../components/layout/MobileNavDrawer";
import { Icon } from "../components/icons/Icon";
import { NAV, PAGE_TITLES } from "../lib/nav";
import { GuideAssistant } from "../features/guide/GuideAssistant";

export function AppShell() {
  const location = useLocation();
  const connection = useApiConnection();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const title =
    PAGE_TITLES[location.pathname] ??
    (location.pathname.startsWith("/library/")
      ? "Document"
      : location.pathname.startsWith("/history/")
        ? "Session"
        : "Grounded Research Desk");

  const connectionLabel =
    connection === "connected" ? "Connected" : connection === "connecting" ? "Connecting…" : "Disconnected";

  return (
    <div className="grd-app">
      <MobileNavDrawer open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} nav={NAV} />
      <aside className="grd-sidebar" aria-label="Primary navigation">
        <div className="grd-brand">
          <div className="grd-brand-mark" aria-hidden />
          <div>
            <div className="grd-brand-title">Grounded Research Desk</div>
            <div className="grd-brand-tagline">Evidence first.</div>
          </div>
        </div>
        {NAV.map((section) => (
          <div className="grd-nav-group" key={section.group}>
            <div className="grd-nav-label">{section.group}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `grd-nav-link${isActive ? " active" : ""}`}
              >
                <Icon name={item.icon} />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </aside>
      <div className="grd-main">
        <header className="grd-topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "var(--grd-space-3)" }}>
            <button
              type="button"
              className="grd-btn grd-btn-secondary grd-menu-btn grd-icon-btn"
              aria-label="Open navigation menu"
              aria-expanded={mobileNavOpen}
              onClick={() => setMobileNavOpen(true)}
            >
              <Icon name="menu" />
            </button>
            <div className="grd-page-title">{title}</div>
          </div>
          <div
            className={`grd-status-pill${connection === "disconnected" ? " error" : ""}`}
            aria-live="polite"
            title={
              connection === "disconnected"
                ? "Start the API: uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
                : "API health check"
            }
          >
            <span
              className={`grd-status-dot ${connection === "connected" ? "ok" : connection === "disconnected" ? "error" : ""}`}
            />
            API {connectionLabel}
          </div>
        </header>
        <Outlet />
      </div>
      <GuideAssistant />
    </div>
  );
}
