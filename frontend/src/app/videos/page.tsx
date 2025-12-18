"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function VideosPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to unified Library page
    router.replace("/content");
  }, [router]);

  return (
    <div className="min-h-screen bg-[var(--bg-base)] flex items-center justify-center">
      <div className="text-center">
        <div className="text-lg font-medium text-[var(--text-primary)]">
          Redirecting to Library...
        </div>
      </div>
    </div>
  );
}
