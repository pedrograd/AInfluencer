"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle, Info, X } from "lucide-react";
import { IconButton } from "./button";

export interface AlertProps {
  title?: string;
  message: string | React.ReactNode;
  variant: "success" | "error" | "info" | "warning";
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

const variantStyles = {
  success: {
    bg: "bg-[var(--success-bg)]",
    border: "border-[var(--success)]",
    text: "text-[var(--success)]",
    icon: CheckCircle2,
  },
  error: {
    bg: "bg-[var(--error-bg)]",
    border: "border-[var(--error)]",
    text: "text-[var(--error)]",
    icon: XCircle,
  },
  info: {
    bg: "bg-[var(--info-bg)]",
    border: "border-[var(--info)]",
    text: "text-[var(--info)]",
    icon: Info,
  },
  warning: {
    bg: "bg-[var(--warning-bg)]",
    border: "border-[var(--warning)]",
    text: "text-[var(--warning)]",
    icon: AlertCircle,
  },
};

export function Alert({
  title,
  message,
  variant,
  action,
  dismissible,
  onDismiss,
  className,
}: AlertProps) {
  const styles = variantStyles[variant];
  const Icon = styles.icon;

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        styles.bg,
        styles.border,
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={cn("h-5 w-5 flex-shrink-0 mt-0.5", styles.text)} />
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={cn("font-semibold mb-1", styles.text)}>{title}</h4>
          )}
          <div className="text-sm text-[var(--text-primary)]">{message}</div>
          {action && (
            <button
              onClick={action.onClick}
              className={cn("mt-3 text-sm font-medium underline", styles.text)}
            >
              {action.label}
            </button>
          )}
        </div>
        {dismissible && onDismiss && (
          <IconButton
            icon={<X className="h-4 w-4" />}
            size="sm"
            variant="ghost"
            onClick={onDismiss}
            aria-label="Dismiss alert"
          />
        )}
      </div>
    </div>
  );
}
