"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface LoadingSkeletonProps {
  variant?: "text" | "card" | "image" | "list";
  count?: number;
  width?: string;
  height?: string;
  className?: string;
}

export function LoadingSkeleton({
  variant = "text",
  count = 1,
  width,
  height,
  className,
}: LoadingSkeletonProps) {
  const baseClasses = "animate-pulse rounded bg-[var(--bg-surface)]";

  if (variant === "text") {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={cn(baseClasses, height || "h-4", width || "w-full")}
            style={{
              width: i === count - 1 ? "75%" : width || "100%",
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div
        className={cn(
          baseClasses,
          height || "h-48",
          width || "w-full",
          className
        )}
      />
    );
  }

  if (variant === "image") {
    return (
      <div
        className={cn(
          baseClasses,
          "aspect-video",
          height || "h-48",
          width || "w-full",
          className
        )}
      />
    );
  }

  if (variant === "list") {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className={cn(baseClasses, "h-12 w-12 rounded-full")} />
            <div className="flex-1 space-y-2">
              <div className={cn(baseClasses, "h-4 w-3/4")} />
              <div className={cn(baseClasses, "h-3 w-1/2")} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return null;
}
