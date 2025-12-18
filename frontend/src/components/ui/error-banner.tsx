"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "./button";

export interface ErrorBannerProps {
  title: string;
  message: string;
  remediation?: {
    label: string;
    onClick: () => void;
  };
  learnMore?: {
    label: string;
    href: string;
  };
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({
  title,
  message,
  remediation,
  learnMore,
  dismissible,
  onDismiss,
  className,
}: ErrorBannerProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-[var(--error)] bg-[var(--error-bg)] p-6",
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-4">
        <AlertTriangle className="h-6 w-6 flex-shrink-0 text-[var(--error)] mt-0.5" />
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-[var(--error)] mb-2">
            {title}
          </h3>
          <p className="text-sm text-[var(--text-primary)] mb-4">{message}</p>
          <div className="flex flex-wrap items-center gap-3">
            {remediation && (
              <PrimaryButton
                onClick={remediation.onClick}
                size="sm"
                className="bg-[var(--error)] hover:bg-[var(--error)]/90"
              >
                {remediation.label}
              </PrimaryButton>
            )}
            {learnMore && (
              <SecondaryButton
                onClick={() => window.open(learnMore.href, "_blank")}
                size="sm"
              >
                {learnMore.label}
              </SecondaryButton>
            )}
          </div>
        </div>
        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            aria-label="Dismiss error"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
