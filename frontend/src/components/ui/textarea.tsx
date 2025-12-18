"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  resize?: "none" | "vertical" | "both";
}

export function Textarea({
  label,
  error,
  helperText,
  required,
  resize = "vertical",
  className,
  id,
  rows = 4,
  ...props
}: TextareaProps) {
  const textareaId =
    id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-[var(--text-primary)] mb-1.5"
        >
          {label}
          {required && <span className="text-[var(--error)] ml-1">*</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        className={cn(
          "w-full rounded-lg border px-4 py-2.5 text-base transition-colors",
          "bg-[var(--bg-elevated)] border-[var(--border-base)] text-[var(--text-primary)]",
          "placeholder:text-[var(--text-muted)]",
          "focus:border-[var(--border-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-offset-2",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          resize === "none" && "resize-none",
          resize === "vertical" && "resize-y",
          resize === "both" && "resize",
          error &&
            "border-[var(--error)] focus:border-[var(--error)] focus:ring-[var(--error)]",
          className
        )}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={
          error || helperText
            ? `${textareaId}-${error ? "error" : "helper"}`
            : undefined
        }
        {...props}
      />
      {error && (
        <p
          id={`${textareaId}-error`}
          className="mt-1.5 text-sm text-[var(--error)]"
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${textareaId}-helper`}
          className="mt-1.5 text-sm text-[var(--text-secondary)]"
        >
          {helperText}
        </p>
      )}
    </div>
  );
}
