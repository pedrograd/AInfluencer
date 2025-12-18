"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface Step {
  id: string;
  label: string;
  completed: boolean;
}

export interface ProgressIndicatorProps {
  value?: number; // 0-100 for linear/circular
  variant: "linear" | "circular" | "steps";
  steps?: Step[];
  label?: string;
  className?: string;
}

export function ProgressIndicator({
  value = 0,
  variant,
  steps,
  label,
  className,
}: ProgressIndicatorProps) {
  if (variant === "linear") {
    return (
      <div className={cn("w-full", className)}>
        {label && (
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {label}
            </span>
            {value !== undefined && (
              <span className="text-sm text-[var(--text-secondary)]">
                {Math.round(value)}%
              </span>
            )}
          </div>
        )}
        <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-surface)]">
          <div
            className="h-full bg-[var(--accent-primary)] transition-all duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          />
        </div>
      </div>
    );
  }

  if (variant === "circular") {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (value / 100) * circumference;

    return (
      <div className={cn("flex flex-col items-center gap-2", className)}>
        <div className="relative h-24 w-24">
          <svg className="h-24 w-24 -rotate-90 transform">
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke="var(--bg-surface)"
              strokeWidth="8"
              fill="none"
            />
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke="var(--accent-primary)"
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className="transition-all duration-300 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {Math.round(value)}%
            </span>
          </div>
        </div>
        {label && (
          <span className="text-sm text-[var(--text-secondary)]">{label}</span>
        )}
      </div>
    );
  }

  if (variant === "steps" && steps) {
    return (
      <div className={cn("w-full", className)}>
        {label && (
          <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
            {label}
          </h3>
        )}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 font-semibold text-sm transition-colors",
                  step.completed
                    ? "border-[var(--success)] bg-[var(--success)] text-white"
                    : "border-[var(--border-base)] bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                )}
              >
                {step.completed ? (
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={cn(
                  "text-sm",
                  step.completed
                    ? "text-[var(--text-primary)] font-medium"
                    : "text-[var(--text-secondary)]"
                )}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
}
