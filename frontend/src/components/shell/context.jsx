import { createContext, useContext } from "react";

export const ShellContext = createContext(null);

export function useAppShell() {
  const context = useContext(ShellContext);

  if (!context) {
    throw new Error("useAppShell must be used within AppShell");
  }

  return context;
}
