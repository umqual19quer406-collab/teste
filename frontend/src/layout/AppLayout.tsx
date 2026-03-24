import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="layout">
      <Sidebar />
      <main>
        <Topbar />
        <div className="page">{children}</div>
      </main>
    </div>
  );
}