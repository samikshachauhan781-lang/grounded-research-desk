import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./AppShell";
import { ToastProvider } from "../components/ui/Toast";
import { WorkspacePage } from "../features/workspace/WorkspacePage";
import { LibraryPage } from "../features/library/LibraryPage";
import { DocumentInspectorPage } from "../features/library/DocumentInspectorPage";
import { SearchPage } from "../features/search/SearchPage";
import { HistoryPage } from "../features/history/HistoryPage";
import { SessionDetailPage } from "../features/history/SessionDetailPage";
import { CollectionsPage } from "../features/library/CollectionsPage";
import { ObservatoryPage } from "../features/evaluation/ObservatoryPage";
import { AgentPage } from "../features/agent/AgentPage";
import { SettingsPage } from "../features/settings/SettingsPage";

export function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<WorkspacePage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="history/:sessionId" element={<SessionDetailPage />} />
            <Route path="library" element={<LibraryPage />} />
            <Route path="library/:documentId" element={<DocumentInspectorPage />} />
            <Route path="collections" element={<CollectionsPage />} />
            <Route path="observatory" element={<ObservatoryPage />} />
            <Route path="agent" element={<AgentPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
