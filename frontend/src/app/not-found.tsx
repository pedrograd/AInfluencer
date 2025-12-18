"use client";

import Link from "next/link";
import { PrimaryButton, SecondaryButton, EmptyState } from "@/components/ui";
import { Home, Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <EmptyState
          icon={<Search className="h-16 w-16" />}
          title="Page Not Found"
          description="The page you're looking for doesn't exist or has been moved."
          action={{
            label: "Go to Dashboard",
            onClick: () => (window.location.href = "/"),
          }}
        />
        <div className="mt-8 space-y-4">
          <div className="text-sm text-[var(--text-secondary)]">
            <p className="mb-2">Common pages:</p>
            <div className="flex flex-wrap justify-center gap-2">
              <Link href="/">
                <SecondaryButton size="sm">Dashboard</SecondaryButton>
              </Link>
              <Link href="/characters">
                <SecondaryButton size="sm">Characters</SecondaryButton>
              </Link>
              <Link href="/generate">
                <SecondaryButton size="sm">Generate</SecondaryButton>
              </Link>
              <Link href="/content">
                <SecondaryButton size="sm">Library</SecondaryButton>
              </Link>
            </div>
          </div>
          <div className="pt-4 border-t border-[var(--border-base)]">
            <Link href="/">
              <PrimaryButton icon={<Home className="h-4 w-4" />}>
                Return Home
              </PrimaryButton>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
