type Props = { name: string; className?: string; size?: number };

export function Icon({ name, className, size = 16 }: Props) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true as const,
  };
  switch (name) {
    case "research":
      return (
        <svg {...common}>
          <path d="M4 19V5a1 1 0 0 1 1-1h9l6 6v9a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1Z" />
          <path d="M14 4v6h6M8 13h8M8 17h5" />
        </svg>
      );
    case "search":
      return (
        <svg {...common}>
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
      );
    case "history":
      return (
        <svg {...common}>
          <path d="M3 12a9 9 0 1 0 3-6.7" />
          <path d="M3 4v5h5M12 7v6l4 2" />
        </svg>
      );
    case "library":
      return (
        <svg {...common}>
          <path d="M4 19a2 2 0 0 0 2 2h12M6 21V5a2 2 0 0 1 2-2h10v18" />
          <path d="M10 8h6M10 12h6" />
        </svg>
      );
    case "collections":
      return (
        <svg {...common}>
          <rect x="3" y="4" width="7" height="7" rx="1" />
          <rect x="14" y="4" width="7" height="7" rx="1" />
          <rect x="3" y="15" width="7" height="7" rx="1" />
          <rect x="14" y="15" width="7" height="7" rx="1" />
        </svg>
      );
    case "observatory":
      return (
        <svg {...common}>
          <path d="M4 18h16M7 18 10 8l2 4 2-3 3 9" />
        </svg>
      );
    case "agent":
      return (
        <svg {...common}>
          <rect x="5" y="7" width="14" height="10" rx="2" />
          <path d="M9 11h.01M15 11h.01M8 17v2M16 17v2M12 7V4" />
        </svg>
      );
    case "settings":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.3.6.9 1 1.6 1.1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
        </svg>
      );
    case "upload":
      return (
        <svg {...common}>
          <path d="M12 16V6M8 10l4-4 4 4M5 20h14" />
        </svg>
      );
    case "menu":
      return (
        <svg {...common}>
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      );
    case "close":
      return (
        <svg {...common}>
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      );
    case "file":
      return (
        <svg {...common}>
          <path d="M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8Z" />
          <path d="M14 3v5h5" />
        </svg>
      );
    case "copy":
      return (
        <svg {...common}>
          <rect x="8" y="8" width="12" height="12" rx="1.5" />
          <path d="M4 16V5a1 1 0 0 1 1-1h11" />
        </svg>
      );
    case "check":
      return (
        <svg {...common}>
          <path d="M5 12l5 5 9-9" />
        </svg>
      );
    case "help":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 2-2.5 2-2.5 3.5" />
          <circle cx="12" cy="17" r="0.5" fill="currentColor" stroke="none" />
        </svg>
      );
    case "bot":
      return (
        <svg {...common}>
          <rect x="5" y="8" width="14" height="11" rx="2" />
          <path d="M9 8V6a3 3 0 0 1 6 0v2M9 13h.01M15 13h.01M9 17h6" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}
