import { useCallback, useEffect, useMemo, useState } from "react";

import { Content } from "./content";
import { ShellContext } from "./context";
import { Header } from "./header";
import { Main } from "./main";
import { Sidebar } from "./sidebar";

function Root({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((open) => !open);
  }, []);

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 768px)");

    const handleChange = () => {
      if (mediaQuery.matches) {
        setSidebarOpen(false);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const value = useMemo(
    () => ({ sidebarOpen, setSidebarOpen, toggleSidebar, closeSidebar }),
    [sidebarOpen, toggleSidebar, closeSidebar],
  );

  return (
    <ShellContext.Provider value={value}>
      <div className="grid h-svh max-h-svh overflow-hidden bg-surface grid-cols-1 grid-rows-[var(--header-height)_1fr] md:grid-cols-[var(--sidebar-width)_1fr]">
        {children}
      </div>
    </ShellContext.Provider>
  );
}

Root.Header = Header;
Root.Main = Main;
Root.Sidebar = Sidebar;
Root.Content = Content;

export { useAppShell } from "./context";
export const AppShell = Root;
