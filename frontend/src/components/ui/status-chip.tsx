"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertCircle, XCircle, Info } from "lucide-react";

export interface StatusChipProps {
  status: "success" | "warning" | "error" | "info";
  label?: string | React.ReactNode;
  icon?: React.ReactNode;
  pulsing?: boolean;
  className?: string;
}

const statusConfig = {
  success: {
    bg: "bg-[var(--success)]",
    text: "text-white",
    defaultLabel: "Healthy",
    icon: CheckCircle2,
  },
  warning: {
    bg: "bg-[var(--warning)]",
    text: "text-white",
    defaultLabel: "Warning",
    icon: AlertCircle,
  },
  error: {
    bg: "bg-[var(--error)]",
    text: "text-white",
    defaultLabel: "Error",
    icon: XCircle,
  },
  info: {
    bg: "bg-[var(--info)]",
    text: "text-white",
    defaultLabel: "Info",
    icon: Info,
  },
};

export function StatusChip({
  status,
  label,
  icon,
  pulsing,
  className,
}: StatusChipProps) {
  const config = statusConfig[status];
  const DefaultIcon = config.icon;
  const displayIcon = icon || <DefaultIcon className="h-3.5 w-3.5" />;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        config.bg,
        config.text,
        pulsing && "animate-pulse",
        className
      )}
    >
      {displayIcon}
      <span>{label || config.defaultLabel}</span>
    </span>
  );
}
