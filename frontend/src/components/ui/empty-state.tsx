"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { PrimaryButton, SecondaryButton } from "./button";

export interface EmptyStateAction {
  label: string;
  onClick: () => void;
}

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action: EmptyStateAction;
  secondaryAction?: EmptyStateAction;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4 text-center",
        className
      )}
    >
      {icon && <div className="mb-4 text-[var(--text-muted)]">{icon}</div>}
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
        {title}
      </h3>
      <p className="text-sm text-[var(--text-secondary)] mb-6 max-w-md">
        {description}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <PrimaryButton onClick={action.onClick} size="md">
          {action.label}
        </PrimaryButton>
        {secondaryAction && (
          <SecondaryButton onClick={secondaryAction.onClick} size="md">
            {secondaryAction.label}
          </SecondaryButton>
        )}
      </div>
    </div>
  );
}
