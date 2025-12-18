"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface SectionCardProps {
  title?: string;
  description?: string | React.ReactNode;
  children: React.ReactNode;
  variant?: "default" | "elevated" | "bordered";
  loading?: boolean;
  empty?: boolean;
  emptyMessage?: string;
  action?: React.ReactNode;
  className?: string;
  id?: string;
}

export function SectionCard({
  title,
  description,
  children,
  variant = "default",
  loading,
  empty,
  emptyMessage = "No content available",
  action,
  className,
  id,
}: SectionCardProps) {
  return (
    <div
      id={id}
      className={cn(
        "rounded-xl border p-6 transition-all",
        "bg-[var(--bg-elevated)] border-[var(--border-base)]",
        variant === "elevated" && "shadow-lg",
        variant === "bordered" && "border-2 border-[var(--border-elevated)]",
        "hover:shadow-md",
        className
      )}
    >
      {(title || description || action) && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex-1">
            {title && (
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                {title}
              </h3>
            )}
            {description && (
              <p className="text-sm text-[var(--text-secondary)]">
                {description}
              </p>
            )}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      {loading ? (
        <div className="space-y-3">
          <div className="h-4 w-3/4 animate-pulse rounded bg-[var(--bg-surface)]" />
          <div className="h-4 w-full animate-pulse rounded bg-[var(--bg-surface)]" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-[var(--bg-surface)]" />
        </div>
      ) : empty ? (
        <div className="py-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">{emptyMessage}</p>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
