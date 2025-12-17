"use client";

import { useEffect, useState } from "react";
import { getWhiteLabelConfig, type WhiteLabelConfig } from "@/lib/api";

const DEFAULT_CONFIG: WhiteLabelConfig = {
  app_name: "AInfluencer",
  app_description: null,
  logo_url: null,
  favicon_url: null,
  primary_color: "#6366f1",
  secondary_color: "#8b5cf6",
  is_active: true,
};

export function WhiteLabelProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<WhiteLabelConfig>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    }

    void loadConfig();
  }, []);

  useEffect(() => {
    if (loading) return;

    // Apply CSS variables for colors
    const root = document.documentElement;
    root.style.setProperty("--color-primary", config.primary_color);
    root.style.setProperty("--color-secondary", config.secondary_color);

    // Update page title
    document.title = config.app_name;

    // Update favicon if provided
    if (config.favicon_url) {
      let link = document.querySelector("link[rel='icon']") as HTMLLinkElement;
      if (!link) {
        link = document.createElement("link");
        link.rel = "icon";
        document.head.appendChild(link);
      }
      link.href = config.favicon_url;
    }
  }, [config, loading]);

  // Don't render children until config is loaded to avoid flash
  if (loading) {
    return <>{children}</>;
  }

  return <>{children}</>;
}
