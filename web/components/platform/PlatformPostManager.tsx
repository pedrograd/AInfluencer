"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface PlatformPost {
  id: string;
  account_id: string;
  platform: string;
  media_id?: string;
  post_type: string;
  caption: string;
  status: string;
  platform_post_id?: string;
  scheduled_at?: string;
  published_at?: string;
  failed_at?: string;
  error_message?: string;
  retry_count: number;
  created_at?: string;
}

interface PlatformAccount {
  id: string;
  platform: string;
  username: string;
}

interface PlatformPostManagerProps {
  mediaId?: string;
  onPostCreated?: () => void;
}

export default function PlatformPostManager({ mediaId, onPostCreated }: PlatformPostManagerProps) {
  const [posts, setPosts] = useState<PlatformPost[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    account_id: "",
    media_id: mediaId || "",
    caption: "",
    post_type: "photo",
    scheduled_at: ""
  });

  useEffect(() => {
    loadAccounts();
    loadPosts();
    if (mediaId) {
      setFormData(prev => ({ ...prev, media_id: mediaId }));
    }
  }, [mediaId]);

  const loadAccounts = async () => {
    try {
      const response = await fetch("/api/platforms/accounts?is_active=true");
      const data = await response.json();
      if (data.success) {
        setAccounts(data.data.accounts || []);
      }
    } catch (err) {
      console.error("Failed to load accounts:", err);
    }
  };

  const loadPosts = async () => {
    try {
      const response = await fetch("/api/platforms/posts");
      const data = await response.json();
      if (data.success) {
        setPosts(data.data.posts || []);
      }
    } catch (err) {
      console.error("Failed to load posts:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: any = {
        account_id: formData.account_id,
        caption: formData.caption,
        post_type: formData.post_type
      };

      if (formData.media_id) {
        payload.media_id = formData.media_id;
      }

      if (formData.scheduled_at) {
        payload.scheduled_at = new Date(formData.scheduled_at).toISOString();
      }

      const response = await fetch("/api/platforms/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (data.success) {
        setShowForm(false);
        setFormData({
          account_id: "",
          media_id: mediaId || "",
          caption: "",
          post_type: "photo",
          scheduled_at: ""
        });
        loadPosts();
        onPostCreated?.();
      } else {
        setError(data.error?.message || "Failed to create post");
      }
    } catch (err: any) {
      setError(err.message || "Failed to create post");
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (postId: string) => {
    if (!confirm("Publish this post now?")) return;

    try {
      const response = await fetch(`/api/platforms/posts/${postId}/publish`, {
        method: "POST"
      });

      const data = await response.json();
      if (data.success) {
        loadPosts();
      } else {
        setError(data.error?.message || "Failed to publish post");
      }
    } catch (err: any) {
      setError(err.message || "Failed to publish post");
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      published: "default",
      pending: "secondary",
      scheduled: "outline",
      failed: "destructive"
    };

    return (
      <Badge variant={variants[status] || "default"} className="capitalize">
        {status}
      </Badge>
    );
  };

  const filteredAccounts = accounts.filter(acc => {
    if (formData.post_type === "reel" || formData.post_type === "video") {
      return acc.platform === "instagram" || acc.platform === "youtube" || acc.platform === "onlyfans";
    }
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Platform Posts</h2>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Create Post"}
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
            <CardTitle>Create Platform Post</CardTitle>
            <CardDescription>Schedule or publish content to your platforms</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="account_id">Platform Account</Label>
                <Select
                  value={formData.account_id}
                  onValueChange={(value) => setFormData({ ...formData, account_id: value })}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select account" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.platform} - {account.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="post_type">Post Type</Label>
                <Select
                  value={formData.post_type}
                  onValueChange={(value) => setFormData({ ...formData, post_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="photo">Photo</SelectItem>
                    <SelectItem value="reel">Reel/Short</SelectItem>
                    <SelectItem value="video">Video</SelectItem>
                    <SelectItem value="story">Story</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="media_id">Media ID (Optional)</Label>
                <Input
                  id="media_id"
                  value={formData.media_id}
                  onChange={(e) => setFormData({ ...formData, media_id: e.target.value })}
                  placeholder="Media item ID"
                />
              </div>

              <div>
                <Label htmlFor="caption">Caption</Label>
                <Textarea
                  id="caption"
                  value={formData.caption}
                  onChange={(e) => setFormData({ ...formData, caption: e.target.value })}
                  rows={4}
                  placeholder="Write your caption here..."
                />
              </div>

              <div>
                <Label htmlFor="scheduled_at">Schedule (Optional)</Label>
                <Input
                  id="scheduled_at"
                  type="datetime-local"
                  value={formData.scheduled_at}
                  onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty to publish immediately
                </p>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {loading ? "Creating..." : "Create Post"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {posts.map((post) => (
          <Card key={post.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="capitalize">{post.platform}</CardTitle>
                  <CardDescription>{post.post_type}</CardDescription>
                </div>
                {getStatusBadge(post.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm">{post.caption}</p>
                {post.platform_post_id && (
                  <p className="text-xs text-muted-foreground">
                    Platform ID: {post.platform_post_id}
                  </p>
                )}
                {post.scheduled_at && (
                  <p className="text-xs text-muted-foreground">
                    Scheduled: {new Date(post.scheduled_at).toLocaleString()}
                  </p>
                )}
                {post.published_at && (
                  <p className="text-xs text-muted-foreground">
                    Published: {new Date(post.published_at).toLocaleString()}
                  </p>
                )}
                {post.error_message && (
                  <Alert variant="destructive">
                    <AlertDescription>{post.error_message}</AlertDescription>
                  </Alert>
                )}
                <div className="flex gap-2 mt-4">
                  {post.status === "pending" || post.status === "scheduled" ? (
                    <Button
                      size="sm"
                      onClick={() => handlePublish(post.id)}
                    >
                      Publish Now
                    </Button>
                  ) : null}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {posts.length === 0 && !showForm && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No posts created yet. Click "Create Post" to get started.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
