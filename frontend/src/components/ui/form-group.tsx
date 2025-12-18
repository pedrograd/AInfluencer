"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface FormGroupProps {
  label?: string;
  description?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormGroup({
  label,
  description,
  error,
  children,
  className,
}: FormGroupProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="block text-sm font-semibold text-[var(--text-primary)]">
          {label}
        </label>
      )}
      {description && (
        <p className="text-sm text-[var(--text-secondary)]">{description}</p>
      )}
      <div className="space-y-4">{children}</div>
      {error && (
        <p className="text-sm text-[var(--error)]" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
