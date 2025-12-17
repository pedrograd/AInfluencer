"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getWhiteLabelConfig, type WhiteLabelConfig } from "@/lib/api";

const DEFAULT_CONFIG: WhiteLabelConfig = {
  app_name: "AInfluencer",
  app_description: "Monitor your AI influencers, track performance, and manage your content automation platform.",
  logo_url: null,
  favicon_url: null,
  primary_color: "#6366f1",
  secondary_color: "#8b5cf6",
  is_active: true,
};

export function DashboardHeader() {
  const [config, setConfig] = useState<WhiteLabelConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    async function loadConfig() {
      try {
        const whiteLabelConfig = await getWhiteLabelConfig();
        if (whiteLabelConfig.is_active) {
          setConfig(whiteLabelConfig);
        }
      } catch (error) {
        console.error("Failed to load white-label config:", error);
        // Use default config on error
      }
    }

    void loadConfig();
  }, []);

  const primaryColor = config.primary_color || "#6366f1";
  const secondaryColor = config.secondary_color || "#8b5cf6";
  const appName = config.app_name || "AInfluencer";
  const appDescription = config.app_description || "Monitor your AI influencers, track performance, and manage your content automation platform.";

  // Update CSS variables for gradient
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--wl-primary", primaryColor);
    root.style.setProperty("--wl-secondary", secondaryColor);
  }, [primaryColor, secondaryColor]);

  return (
    <div className="mb-6 sm:mb-8">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex-1">
          <h1
            className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight bg-clip-text text-transparent"
            style={{
              backgroundImage: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            {appName} Dashboard
          </h1>
          <p className="mt-2 max-w-2xl text-xs sm:text-sm leading-6 text-zinc-600">
            {appDescription}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Link
            href="/characters/create"
            className="w-full sm:w-auto shrink-0 rounded-lg px-4 sm:px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 transition-colors shadow-sm text-center"
            style={{ backgroundColor: primaryColor }}
          >
            + New Character
          </Link>
          <Link
            href="/installer"
            className="w-full sm:w-auto shrink-0 rounded-lg border border-zinc-300 bg-white px-4 sm:px-5 py-2.5 text-sm font-semibold text-zinc-700 hover:bg-zinc-50 transition-colors text-center"
          >
            Settings
          </Link>
        </div>
      </div>
    </div>
  );
}
