"use client";

import React, { useEffect } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle, Info, X } from "lucide-react";
import { IconButton } from "./button";

export interface ToastProps {
  message: string;
  variant: "success" | "error" | "info" | "warning";
  duration?: number;
  onDismiss?: () => void;
  className?: string;
}

const variantStyles = {
  success: {
    bg: "bg-[var(--success)]",
    icon: CheckCircle2,
  },
  error: {
    bg: "bg-[var(--error)]",
    icon: XCircle,
  },
  info: {
    bg: "bg-[var(--info)]",
    icon: Info,
  },
  warning: {
    bg: "bg-[var(--warning)]",
    icon: AlertCircle,
  },
};

export function Toast({
  message,
  variant,
  duration = 5000,
  onDismiss,
  className,
}: ToastProps) {
  useEffect(() => {
    if (duration > 0 && onDismiss) {
      const timer = setTimeout(() => {
        onDismiss();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onDismiss]);

  const styles = variantStyles[variant];
  const Icon = styles.icon;

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg",
        styles.bg,
        "text-white",
        "animate-in slide-in-from-top-5 fade-in",
        className
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{message}</p>
      {onDismiss && (
        <IconButton
          icon={<X className="h-4 w-4" />}
          size="sm"
          variant="ghost"
          onClick={onDismiss}
          aria-label="Dismiss toast"
          className="text-white hover:bg-white/20"
        />
      )}
    </div>
  );
}

// Toast Container for managing multiple toasts
export interface ToastContainerProps {
  toasts: Array<ToastProps & { id: string }>;
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          onDismiss={() => onDismiss(toast.id)}
        />
      ))}
    </div>
  );
}
