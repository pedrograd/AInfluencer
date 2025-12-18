"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Settings,
  UserPlus,
  Sparkles,
  Library,
  Package,
  BarChart3,
  Workflow,
  Wrench,
  ChevronDown,
} from "lucide-react";

type NavItem = {
  href: string;
  label: string;
  icon: React.ReactNode;
  description: string;
};

const MAIN_NAV_ITEMS: NavItem[] = [
  {
    href: "/installer",
    label: "Setup",
    icon: <Settings className="h-4 w-4" />,
    description: "Install & configure system",
  },
  {
    href: "/characters",
    label: "Create",
    icon: <UserPlus className="h-4 w-4" />,
    description: "Create & manage characters",
  },
  {
    href: "/generate",
    label: "Generate",
    icon: <Sparkles className="h-4 w-4" />,
    description: "Generate images & videos",
  },
  {
    href: "/content",
    label: "Library",
    icon: <Library className="h-4 w-4" />,
    description: "View generated content",
  },
];

const ADVANCED_NAV_ITEMS: NavItem[] = [
  {
    href: "/models",
    label: "Models",
    icon: <Package className="h-4 w-4" />,
    description: "Manage AI models",
  },
  {
    href: "/analytics",
    label: "Analytics",
    icon: <BarChart3 className="h-4 w-4" />,
    description: "Performance metrics",
  },
  {
    href: "/comfyui",
    label: "ComfyUI",
    icon: <Wrench className="h-4 w-4" />,
    description: "ComfyUI management",
  },
  // Note: /workflows and /settings are hidden until implemented
];

export function MainNavigation() {
  const pathname = usePathname();
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(href);
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border-base)] bg-[var(--bg-elevated)] backdrop-blur-sm">
      <div className="container mx-auto px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link
              href="/"
              className="flex items-center gap-2 text-xl font-bold text-[var(--text-primary)] transition-colors hover:text-[var(--accent-primary)]"
            >
              AInfluencer
            </Link>
          </div>

          {/* Main Navigation */}
          <div className="flex items-center gap-1">
            {MAIN_NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all",
                  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] focus-visible:outline-offset-2",
                  isActive(item.href)
                    ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] hover:text-[var(--text-primary)]"
                )}
                title={item.description}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}

            {/* Advanced Toggle */}
            <div className="relative">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-all",
                  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] focus-visible:outline-offset-2",
                  showAdvanced
                    ? "bg-[var(--bg-surface)] text-[var(--text-primary)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] hover:text-[var(--text-primary)]"
                )}
                aria-expanded={showAdvanced}
                aria-haspopup="true"
              >
                <span>Advanced</span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    showAdvanced && "rotate-180"
                  )}
                />
              </button>

              {/* Advanced Navigation Dropdown */}
              {showAdvanced && (
                <div className="absolute right-0 top-full mt-2 w-56 rounded-lg border border-[var(--border-base)] bg-[var(--bg-elevated)] shadow-lg">
                  <div className="p-2">
                    {ADVANCED_NAV_ITEMS.map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--border-focus)] focus-visible:outline-offset-2",
                          isActive(item.href)
                            ? "bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                            : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] hover:text-[var(--text-primary)]"
                        )}
                        title={item.description}
                        onClick={() => setShowAdvanced(false)}
                      >
                        {item.icon}
                        <span>{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
