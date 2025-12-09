"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AutomationConfig {
  count: number;
  content_type: "image" | "video";
  character_id?: string;
  auto_quality_check: boolean;
  min_quality_score: number;
  auto_retry: boolean;
  max_retries: number;
  platform?: string;
  daily_content_count: number;
  post_interval_hours: number;
}

interface GenerationResult {
  job_id: string;
  media_id?: string;
  media_path?: string;
  quality_score?: number;
  status: "completed" | "failed" | "processing";
  error?: string;
}

export default function AutomationPage() {
  const [config, setConfig] = useState<AutomationConfig>({
    count: 10,
    content_type: "image",
    auto_quality_check: true,
    min_quality_score: 8.0,
    auto_retry: true,
    max_retries: 3,
    daily_content_count: 10,
    post_interval_hours: 2,
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState<GenerationResult[]>([]);
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    fetchMetrics();
    fetchAlerts();
    const interval = setInterval(() => {
      fetchMetrics();
      fetchAlerts();
    }, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/monitoring/metrics`);
      const data = await response.json();
      if (data.success) {
        setMetrics(data.data);
      }
    } catch (error) {
      console.error("Error fetching metrics:", error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/monitoring/alerts`);
      const data = await response.json();
      if (data.success) {
        setAlerts(data.data);
      }
    } catch (error) {
      console.error("Error fetching alerts:", error);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setResults([]);
    setProgress(0);

    try {
      const response = await fetch(`${API_BASE}/api/automation/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          count: config.count,
          content_type: config.content_type,
          character_id: config.character_id,
          settings: {
            auto_quality_check: config.auto_quality_check,
            min_quality_score: config.min_quality_score,
            auto_retry: config.auto_retry,
            max_retries: config.max_retries,
          },
        }),
      });

      const data = await response.json();
      if (data.success) {
        setResults(data.data.results || []);
        setProgress(100);
      } else {
        alert("Generation failed: " + (data.error?.message || "Unknown error"));
      }
    } catch (error) {
      console.error("Generation error:", error);
      alert("Generation failed: " + error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCompleteAutomation = async (workflow: "daily" | "batch") => {
    setIsGenerating(true);
    setResults([]);

    try {
      const response = await fetch(`${API_BASE}/api/automation/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow,
          count: config.daily_content_count,
          content_type: config.content_type,
          character_id: config.character_id,
          platform: config.platform,
          daily_content_count: config.daily_content_count,
          post_interval_hours: config.post_interval_hours,
          generation_settings: {
            auto_quality_check: config.auto_quality_check,
            min_quality_score: config.min_quality_score,
            auto_retry: config.auto_retry,
            max_retries: config.max_retries,
          },
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert(`Automation complete! Generated: ${data.data.generated?.length || 0}, Approved: ${data.data.approved?.length || 0}, Posted: ${data.data.posted?.posted || 0}`);
        fetchMetrics();
      } else {
        alert("Automation failed: " + (data.error?.message || "Unknown error"));
      }
    } catch (error) {
      console.error("Automation error:", error);
      alert("Automation failed: " + error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Automation Workflows</h1>
          <p className="text-muted-foreground mt-2">
            Complete automation from generation to posting
          </p>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, idx) => (
            <Alert key={idx} variant={alert.severity === "warning" ? "destructive" : "default"}>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <div className="text-2xl font-bold">{metrics.generated || 0}</div>
                <div className="text-sm text-muted-foreground">Generated</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{metrics.posted || 0}</div>
                <div className="text-sm text-muted-foreground">Posted</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {metrics.quality_avg?.toFixed(1) || "0.0"}
                </div>
                <div className="text-sm text-muted-foreground">Avg Quality</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {((metrics.success_rate || 0) * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Success Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="generate" className="space-y-4">
        <TabsList>
          <TabsTrigger value="generate">Content Generation</TabsTrigger>
          <TabsTrigger value="complete">Complete Automation</TabsTrigger>
          <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="generate" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Automated Content Generation</CardTitle>
              <CardDescription>
                Generate content with automatic quality checks and retry logic
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Count</Label>
                  <Input
                    type="number"
                    value={config.count}
                    onChange={(e) =>
                      setConfig({ ...config, count: parseInt(e.target.value) || 0 })
                    }
                  />
                </div>
                <div>
                  <Label>Content Type</Label>
                  <Select
                    value={config.content_type}
                    onValueChange={(value: "image" | "video") =>
                      setConfig({ ...config, content_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="image">Image</SelectItem>
                      <SelectItem value="video">Video</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Auto Quality Check</Label>
                  <Switch
                    checked={config.auto_quality_check}
                    onCheckedChange={(checked) =>
                      setConfig({ ...config, auto_quality_check: checked })
                    }
                  />
                </div>
                {config.auto_quality_check && (
                  <div>
                    <Label>Minimum Quality Score: {config.min_quality_score}</Label>
                    <Slider
                      value={[config.min_quality_score]}
                      onValueChange={([value]) =>
                        setConfig({ ...config, min_quality_score: value })
                      }
                      min={0}
                      max={10}
                      step={0.1}
                    />
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Auto Retry</Label>
                  <Switch
                    checked={config.auto_retry}
                    onCheckedChange={(checked) =>
                      setConfig({ ...config, auto_retry: checked })
                    }
                  />
                </div>
                {config.auto_retry && (
                  <div>
                    <Label>Max Retries: {config.max_retries}</Label>
                    <Slider
                      value={[config.max_retries]}
                      onValueChange={([value]) =>
                        setConfig({ ...config, max_retries: value })
                      }
                      min={1}
                      max={5}
                      step={1}
                    />
                  </div>
                )}
              </div>

              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full"
              >
                {isGenerating ? "Generating..." : "Start Generation"}
              </Button>

              {isGenerating && (
                <Progress value={progress} className="w-full" />
              )}

              {results.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold">Results</h3>
                  <div className="space-y-1">
                    <div>Total: {results.length}</div>
                    <div>
                      Completed: {results.filter((r) => r.status === "completed").length}
                    </div>
                    <div>
                      Failed: {results.filter((r) => r.status === "failed").length}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="complete" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Complete Automation</CardTitle>
              <CardDescription>
                Run complete workflow: Generate → Quality Check → Approve → Schedule → Post
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Daily Content Count</Label>
                  <Input
                    type="number"
                    value={config.daily_content_count}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        daily_content_count: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <Label>Post Interval (hours)</Label>
                  <Input
                    type="number"
                    value={config.post_interval_hours}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        post_interval_hours: parseFloat(e.target.value) || 2,
                      })
                    }
                  />
                </div>
              </div>

              <div>
                <Label>Platform</Label>
                <Select
                  value={config.platform}
                  onValueChange={(value) => setConfig({ ...config, platform: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instagram">Instagram</SelectItem>
                    <SelectItem value="twitter">Twitter</SelectItem>
                    <SelectItem value="onlyfans">OnlyFans</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => handleCompleteAutomation("daily")}
                  disabled={isGenerating}
                  className="flex-1"
                >
                  Run Daily Automation
                </Button>
                <Button
                  onClick={() => handleCompleteAutomation("batch")}
                  disabled={isGenerating}
                  className="flex-1"
                  variant="outline"
                >
                  Run Batch Generation
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scheduling" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Content Scheduling</CardTitle>
              <CardDescription>Schedule content for automatic posting</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Scheduling interface will be implemented here
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Monitoring</CardTitle>
              <CardDescription>Monitor system health and performance</CardDescription>
            </CardHeader>
            <CardContent>
              {metrics ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Generated</div>
                      <div className="text-2xl font-bold">{metrics.generated || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Posted</div>
                      <div className="text-2xl font-bold">{metrics.posted || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Failed</div>
                      <div className="text-2xl font-bold">{metrics.failed || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Avg Quality</div>
                      <div className="text-2xl font-bold">
                        {metrics.quality_avg?.toFixed(1) || "0.0"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">Loading metrics...</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
