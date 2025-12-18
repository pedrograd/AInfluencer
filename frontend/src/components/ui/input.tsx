"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  icon?: React.ReactNode;
}

export function Input({
  label,
  error,
  helperText,
  required,
  icon,
  className,
  id,
  ...props
}: InputProps) {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-[var(--text-primary)] mb-1.5"
        >
          {label}
          {required && <span className="text-[var(--error)] ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">
            {icon}
          </div>
        )}
        <input
          id={inputId}
          className={cn(
            "w-full rounded-lg border px-4 py-2.5 text-base transition-colors",
            "bg-[var(--bg-elevated)] border-[var(--border-base)] text-[var(--text-primary)]",
            "placeholder:text-[var(--text-muted)]",
            "focus:border-[var(--border-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            icon && "pl-10",
            error &&
              "border-[var(--error)] focus:border-[var(--error)] focus:ring-[var(--error)]",
            className
          )}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={
            error || helperText
              ? `${inputId}-${error ? "error" : "helper"}`
              : undefined
          }
          {...props}
        />
      </div>
      {error && (
        <p
          id={`${inputId}-error`}
          className="mt-1.5 text-sm text-[var(--error)]"
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${inputId}-helper`}
          className="mt-1.5 text-sm text-[var(--text-secondary)]"
        >
          {helperText}
        </p>
      )}
    </div>
  );
}
