"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children: React.ReactNode;
  showBreadcrumbs?: boolean;
  statusBar?: React.ReactNode;
  className?: string;
}

export function AppShell({
  children,
  showBreadcrumbs,
  statusBar,
  className,
}: AppShellProps) {
  return (
    <div className={cn("min-h-screen bg-[var(--bg-base)]", className)}>
      {/* Status Bar (Optional) */}
      {statusBar && (
        <div className="border-b border-[var(--border-base)] bg-[var(--bg-surface)]">
          <div className="container mx-auto px-6 py-2">{statusBar}</div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
