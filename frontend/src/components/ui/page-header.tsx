"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface Tab {
  id: string;
  label: string;
  href?: string;
  onClick?: () => void;
}

export interface PageHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  tabs?: Tab[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  className?: string;
}

export function PageHeader({
  title,
  description,
  action,
  tabs,
  activeTab,
  onTabChange,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("mb-8", className)}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
            {title}
          </h1>
          {description && (
            <p className="text-base text-[var(--text-secondary)]">
              {description}
            </p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
      {tabs && tabs.length > 0 && (
        <div className="border-b border-[var(--border-base)]">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              const content = (
                <span
                  className={cn(
                    "whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors",
                    isActive
                      ? "border-[var(--accent-primary)] text-[var(--accent-primary)]"
                      : "border-transparent text-[var(--text-secondary)] hover:border-[var(--border-base)] hover:text-[var(--text-primary)]"
                  )}
                >
                  {tab.label}
                </span>
              );

              if (tab.href) {
                return (
                  <a key={tab.id} href={tab.href}>
                    {content}
                  </a>
                );
              }

              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    onTabChange?.(tab.id);
                    tab.onClick?.();
                  }}
                  className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] focus-visible:outline-offset-2"
                >
                  {content}
                </button>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );
}
