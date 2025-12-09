"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PlatformAccountManager from "@/components/platform/PlatformAccountManager";
import PlatformPostManager from "@/components/platform/PlatformPostManager";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function PlatformsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Platform Integration</h1>
        <p className="text-muted-foreground">
          Connect and manage your social media accounts. Schedule and publish content across Instagram, Twitter, Facebook, Telegram, OnlyFans, and YouTube.
        </p>
      </div>

      <Tabs defaultValue="accounts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="accounts">Accounts</TabsTrigger>
          <TabsTrigger value="posts">Posts</TabsTrigger>
          <TabsTrigger value="rate-limits">Rate Limits</TabsTrigger>
        </TabsList>

        <TabsContent value="accounts" className="space-y-4">
          <PlatformAccountManager key={refreshKey} onAccountCreated={handleRefresh} />
        </TabsContent>

        <TabsContent value="posts" className="space-y-4">
          <PlatformPostManager key={refreshKey} />
        </TabsContent>

        <TabsContent value="rate-limits" className="space-y-4">
          <RateLimitsView />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RateLimitsView() {
  const [rateLimits, setRateLimits] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  const loadRateLimits = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/platforms/rate-limits");
      const data = await response.json();
      if (data.success) {
        setRateLimits(data.data.platforms || {});
      }
    } catch (err) {
      console.error("Failed to load rate limits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRateLimits();
  }, []);

  const platforms = [
    { key: "instagram", name: "Instagram" },
    { key: "twitter", name: "Twitter/X" },
    { key: "facebook", name: "Facebook" },
    { key: "telegram", name: "Telegram" },
    { key: "onlyfans", name: "OnlyFans" },
    { key: "youtube", name: "YouTube" }
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Rate Limits</h2>
        <button
          onClick={loadRateLimits}
          disabled={loading}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {platforms.map((platform) => {
          const limits = rateLimits[platform.key] || {};
          return (
            <Card key={platform.key}>
              <CardHeader>
                <CardTitle>{platform.name}</CardTitle>
                <CardDescription>Rate limit information</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(limits).map(([action, config]: [string, any]) => (
                    <div key={action} className="text-sm">
                      <div className="font-semibold capitalize">{action}</div>
                      <div className="text-muted-foreground">
                        {config.max} per {Math.floor(config.window / 3600)}h
                      </div>
                    </div>
                  ))}
                  {Object.keys(limits).length === 0 && (
                    <p className="text-sm text-muted-foreground">No rate limits configured</p>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
