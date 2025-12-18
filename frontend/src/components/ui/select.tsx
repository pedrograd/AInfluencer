"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  label?: string;
  options: SelectOption[];
  error?: string;
  helperText?: string;
  required?: boolean;
  placeholder?: string;
}

export function Select({
  label,
  options,
  error,
  helperText,
  required,
  placeholder,
  className,
  id,
  ...props
}: SelectProps) {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-[var(--text-primary)] mb-1.5"
        >
          {label}
          {required && <span className="text-[var(--error)] ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          className={cn(
            "w-full appearance-none rounded-lg border px-4 py-2.5 pr-10 text-base transition-colors",
            "bg-[var(--bg-elevated)] border-[var(--border-base)] text-[var(--text-primary)]",
            "focus:border-[var(--border-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--border-focus)] focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            error &&
              "border-[var(--error)] focus:border-[var(--error)] focus:ring-[var(--error)]",
            className
          )}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={
            error || helperText
              ? `${selectId}-${error ? "error" : "helper"}`
              : undefined
          }
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[var(--text-muted)]"
          aria-hidden="true"
        />
      </div>
      {error && (
        <p
          id={`${selectId}-error`}
          className="mt-1.5 text-sm text-[var(--error)]"
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${selectId}-helper`}
          className="mt-1.5 text-sm text-[var(--text-secondary)]"
        >
          {helperText}
        </p>
      )}
    </div>
  );
}
