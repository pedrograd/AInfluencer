"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface Trend {
  value: number;
  label: string;
}

export interface MetricCardProps {
  label: string;
  value: string | number | React.ReactNode;
  trend?: Trend;
  icon?: React.ReactNode;
  variant?: "default" | "icon" | "chart";
  className?: string;
}

export function MetricCard({
  label,
  value,
  trend,
  icon,
  variant = "default",
  className,
}: MetricCardProps) {
  const isPositive = trend && trend.value > 0;
  const isNegative = trend && trend.value < 0;

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border-base)] bg-[var(--bg-elevated)] p-6 transition-all hover:shadow-md",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {icon && variant === "icon" && (
              <span className="text-[var(--text-muted)]">{icon}</span>
            )}
            <p className="text-sm font-medium text-[var(--text-secondary)]">
              {label}
            </p>
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)] mb-1">
            {value}
          </p>
          {trend && (
            <div className="flex items-center gap-1">
              <span
                className={cn(
                  "text-xs font-medium",
                  isPositive && "text-[var(--success)]",
                  isNegative && "text-[var(--error)]",
                  !isPositive && !isNegative && "text-[var(--text-muted)]"
                )}
              >
                {isPositive && "+"}
                {trend.value}%
              </span>
              <span className="text-xs text-[var(--text-muted)]">
                {trend.label}
              </span>
            </div>
          )}
        </div>
        {icon && variant !== "icon" && (
          <div className="flex-shrink-0 text-[var(--text-muted)]">{icon}</div>
        )}
      </div>
    </div>
  );
}
