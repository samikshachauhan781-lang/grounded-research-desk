import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import type { NavSection } from "../../lib/nav";
import { Icon } from "../icons/Icon";

type Props = {
  open: boolean;
  onClose: () => void;
  nav: NavSection[];
};

export function MobileNavDrawer({ open, onClose, nav }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="grd-drawer-root" role="presentation">
      <button type="button" className="grd-drawer-backdrop" aria-label="Close navigation" onClick={onClose} />
      <nav className="grd-drawer-panel" aria-label="Mobile navigation">
        <div className="grd-drawer-header">
          <span className="grd-brand-title">Navigate</span>
          <button
            ref={closeRef}
            type="button"
            className="grd-btn grd-btn-secondary grd-icon-btn"
            onClick={onClose}
            aria-label="Close menu"
          >
            <Icon name="close" />
          </button>
        </div>
        {nav.map((section) => (
          <div className="grd-nav-group" key={section.group}>
            <div className="grd-nav-label">{section.group}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `grd-nav-link${isActive ? " active" : ""}`}
                onClick={onClose}
              >
                <Icon name={item.icon} />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </div>
  );
}
