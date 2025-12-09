"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface PlatformAccount {
  id: string;
  platform: string;
  username: string;
  display_name?: string;
  is_active: boolean;
  last_used_at?: string;
  created_at?: string;
}

interface PlatformAccountManagerProps {
  onAccountCreated?: () => void;
}

export default function PlatformAccountManager({ onAccountCreated }: PlatformAccountManagerProps) {
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    platform: "",
    username: "",
    display_name: "",
    auth_type: "browser",
    credentials: {} as Record<string, any>
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await fetch("/api/platforms/accounts");
      const data = await response.json();
      if (data.success) {
        setAccounts(data.data.accounts || []);
      }
    } catch (err) {
      console.error("Failed to load accounts:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/platforms/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      if (data.success) {
        setShowForm(false);
        setFormData({
          platform: "",
          username: "",
          display_name: "",
          auth_type: "browser",
          credentials: {}
        });
        loadAccounts();
        onAccountCreated?.();
      } else {
        setError(data.error?.message || "Failed to create account");
      }
    } catch (err: any) {
      setError(err.message || "Failed to create account");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (accountId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/platforms/accounts/${accountId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !isActive })
      });

      if (response.ok) {
        loadAccounts();
      }
    } catch (err) {
      console.error("Failed to update account:", err);
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm("Are you sure you want to delete this account?")) return;

    try {
      const response = await fetch(`/api/platforms/accounts/${accountId}`, {
        method: "DELETE"
      });

      if (response.ok) {
        loadAccounts();
      }
    } catch (err) {
      console.error("Failed to delete account:", err);
    }
  };

  const platforms = [
    { value: "instagram", label: "Instagram" },
    { value: "twitter", label: "Twitter/X" },
    { value: "facebook", label: "Facebook" },
    { value: "telegram", label: "Telegram" },
    { value: "onlyfans", label: "OnlyFans" },
    { value: "youtube", label: "YouTube" }
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Platform Accounts</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add Account"}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add Platform Account</CardTitle>
            <CardDescription>Connect your social media accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="platform">Platform</Label>
                <Select
                  value={formData.platform}
                  onValueChange={(value) => setFormData({ ...formData, platform: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    {platforms.map((platform) => (
                      <SelectItem key={platform.value} value={platform.value}>
                        {platform.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="display_name">Display Name (Optional)</Label>
                <Input
                  id="display_name"
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="auth_type">Authentication Type</Label>
                <Select
                  value={formData.auth_type}
                  onValueChange={(value) => setFormData({ ...formData, auth_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="browser">Browser Automation</SelectItem>
                    <SelectItem value="api">API (OAuth/Keys)</SelectItem>
                    <SelectItem value="session">Session/Cookies</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? "Creating..." : "Create Account"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map((account) => (
          <Card key={account.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="capitalize">{account.platform}</CardTitle>
                  <CardDescription>{account.username}</CardDescription>
                </div>
                <Switch
                  checked={account.is_active}
                  onCheckedChange={() => handleToggleActive(account.id, account.is_active)}
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {account.display_name && (
                  <p className="text-sm text-muted-foreground">{account.display_name}</p>
                )}
                {account.last_used_at && (
                  <p className="text-xs text-muted-foreground">
                    Last used: {new Date(account.last_used_at).toLocaleDateString()}
                  </p>
                )}
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(account.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {accounts.length === 0 && !showForm && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No platform accounts connected. Click "Add Account" to get started.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
