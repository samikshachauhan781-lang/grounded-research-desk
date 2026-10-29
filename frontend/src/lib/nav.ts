export type NavItem = { to: string; label: string; end?: boolean; icon: string };
export type NavSection = { group: string; items: NavItem[] };

export const NAV: NavSection[] = [
  {
    group: "Workspace",
    items: [
      { to: "/", label: "Research", end: true, icon: "research" },
      { to: "/search", label: "Search", icon: "search" },
      { to: "/history", label: "History", icon: "history" },
    ],
  },
  {
    group: "Knowledge",
    items: [
      { to: "/library", label: "Library", icon: "library" },
      { to: "/collections", label: "Collections", icon: "collections" },
    ],
  },
  {
    group: "Quality",
    items: [{ to: "/observatory", label: "Observatory", icon: "observatory" }],
  },
  {
    group: "Automation",
    items: [{ to: "/agent", label: "Agent", icon: "agent" }],
  },
  {
    group: "System",
    items: [{ to: "/settings", label: "Settings", icon: "settings" }],
  },
];

export const PAGE_TITLES: Record<string, string> = {
  "/": "Research",
  "/search": "Search",
  "/history": "History",
  "/library": "Library",
  "/collections": "Collections",
  "/observatory": "Observatory",
  "/agent": "Agent",
  "/settings": "Settings",
};
