'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Settings as SettingsIcon, Save, RefreshCw } from 'lucide-react'
import { backendAPI } from '@/lib/api/backend'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Settings {
  generation: {
    default_model: string
    default_quality: 'fast' | 'balanced' | 'ultra'
    default_steps: number
    default_cfg_scale: number
    auto_upscale: boolean
    auto_face_restore: boolean
  }
  storage: {
    media_location: string
    auto_organize: boolean
    cleanup_enabled: boolean
    backup_enabled: boolean
  }
  performance: {
    batch_size: number
    queue_priority: 'low' | 'normal' | 'high'
    gpu_memory_optimization: boolean
    cache_enabled: boolean
  }
  ui: {
    theme: 'dark' | 'light'
    language: string
    notifications: boolean
    keyboard_shortcuts: boolean
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${API_BASE}/api/settings`)
      const data = await response.json()
      if (data.success) {
        setSettings(data.data)
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const saveSettings = async () => {
    if (!settings) return

    try {
      setIsSaving(true)
      setSaveStatus('idle')
      const response = await fetch(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      })
      const data = await response.json()
      if (data.success) {
        setSaveStatus('success')
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaveStatus('error')
    } finally {
      setIsSaving(false)
    }
  }

  const updateSetting = (section: keyof Settings, key: string, value: any) => {
    if (!settings) return
    setSettings({
      ...settings,
      [section]: {
        ...settings[section],
        [key]: value,
      },
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Failed to load settings</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Configure application settings and preferences
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={loadSettings}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button onClick={saveSettings} disabled={isSaving}>
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>

      {saveStatus === 'success' && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-green-500">
          Settings saved successfully!
        </div>
      )}

      {saveStatus === 'error' && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-500">
          Failed to save settings. Please try again.
        </div>
      )}

      <Tabs defaultValue="generation" className="space-y-4">
        <TabsList>
          <TabsTrigger value="generation">Generation</TabsTrigger>
          <TabsTrigger value="storage">Storage</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="ui">UI</TabsTrigger>
        </TabsList>

        {/* Generation Settings */}
        <TabsContent value="generation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generation Settings</CardTitle>
              <CardDescription>
                Configure default generation parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="default_model">Default Model</Label>
                <Select
                  value={settings.generation.default_model}
                  onValueChange={(value) => updateSetting('generation', 'default_model', value)}
                >
                  <SelectTrigger id="default_model">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="realisticVisionV60_v60B1.safetensors">Realistic Vision V6.0</SelectItem>
                    <SelectItem value="flux1-schnell.safetensors">Flux.1 [schnell]</SelectItem>
                    <SelectItem value="flux1-dev.safetensors">Flux.1 [dev]</SelectItem>
                    <SelectItem value="juggernautXL_v9.safetensors">Juggernaut XL V9</SelectItem>
                    <SelectItem value="v1-5-pruned.safetensors">Stable Diffusion 1.5</SelectItem>
                    <SelectItem value="v2-1_768-ema-pruned.safetensors">Stable Diffusion 2.1</SelectItem>
                    <SelectItem value="stable_cascade_stage_c.safetensors">Stable Cascade</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="default_quality">Default Quality</Label>
                <Select
                  value={settings.generation.default_quality}
                  onValueChange={(value) => updateSetting('generation', 'default_quality', value)}
                >
                  <SelectTrigger id="default_quality">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fast">Fast</SelectItem>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="ultra">Ultra Quality</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="default_steps">Default Steps: {settings.generation.default_steps}</Label>
                <Slider
                  id="default_steps"
                  min={20}
                  max={100}
                  step={5}
                  value={[settings.generation.default_steps]}
                  onValueChange={(value) => updateSetting('generation', 'default_steps', value[0])}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="default_cfg_scale">Default CFG Scale: {settings.generation.default_cfg_scale}</Label>
                <Slider
                  id="default_cfg_scale"
                  min={1}
                  max={20}
                  step={0.5}
                  value={[settings.generation.default_cfg_scale]}
                  onValueChange={(value) => updateSetting('generation', 'default_cfg_scale', value[0])}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto_upscale">Auto-Upscale</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically upscale generated images
                  </p>
                </div>
                <Switch
                  id="auto_upscale"
                  checked={settings.generation.auto_upscale}
                  onCheckedChange={(checked) => updateSetting('generation', 'auto_upscale', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto_face_restore">Auto Face Restoration</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically restore faces in generated images
                  </p>
                </div>
                <Switch
                  id="auto_face_restore"
                  checked={settings.generation.auto_face_restore}
                  onCheckedChange={(checked) => updateSetting('generation', 'auto_face_restore', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Storage Settings */}
        <TabsContent value="storage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Storage Settings</CardTitle>
              <CardDescription>
                Configure media storage and organization
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="media_location">Media Location</Label>
                <Input
                  id="media_location"
                  value={settings.storage.media_location}
                  onChange={(e) => updateSetting('storage', 'media_location', e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Directory where media files are stored
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto_organize">Auto-Organize</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically organize media by date/character
                  </p>
                </div>
                <Switch
                  id="auto_organize"
                  checked={settings.storage.auto_organize}
                  onCheckedChange={(checked) => updateSetting('storage', 'auto_organize', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="cleanup_enabled">Auto Cleanup</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically delete low-quality content
                  </p>
                </div>
                <Switch
                  id="cleanup_enabled"
                  checked={settings.storage.cleanup_enabled}
                  onCheckedChange={(checked) => updateSetting('storage', 'cleanup_enabled', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="backup_enabled">Automatic Backups</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable automatic backups of your content
                  </p>
                </div>
                <Switch
                  id="backup_enabled"
                  checked={settings.storage.backup_enabled}
                  onCheckedChange={(checked) => updateSetting('storage', 'backup_enabled', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Settings */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Settings</CardTitle>
              <CardDescription>
                Optimize generation performance and resource usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="batch_size">Batch Size: {settings.performance.batch_size}</Label>
                <Slider
                  id="batch_size"
                  min={1}
                  max={10}
                  step={1}
                  value={[settings.performance.batch_size]}
                  onValueChange={(value) => updateSetting('performance', 'batch_size', value[0])}
                />
                <p className="text-sm text-muted-foreground">
                  Number of images to generate at once
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="queue_priority">Queue Priority</Label>
                <Select
                  value={settings.performance.queue_priority}
                  onValueChange={(value) => updateSetting('performance', 'queue_priority', value)}
                >
                  <SelectTrigger id="queue_priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="gpu_memory_optimization">GPU Memory Optimization</Label>
                  <p className="text-sm text-muted-foreground">
                    Optimize GPU memory usage
                  </p>
                </div>
                <Switch
                  id="gpu_memory_optimization"
                  checked={settings.performance.gpu_memory_optimization}
                  onCheckedChange={(checked) => updateSetting('performance', 'gpu_memory_optimization', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="cache_enabled">Enable Caching</Label>
                  <p className="text-sm text-muted-foreground">
                    Cache generated content for faster access
                  </p>
                </div>
                <Switch
                  id="cache_enabled"
                  checked={settings.performance.cache_enabled}
                  onCheckedChange={(checked) => updateSetting('performance', 'cache_enabled', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* UI Settings */}
        <TabsContent value="ui" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>UI Settings</CardTitle>
              <CardDescription>
                Customize the user interface
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <Select
                  value={settings.ui.theme}
                  onValueChange={(value) => updateSetting('ui', 'theme', value)}
                >
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select
                  value={settings.ui.language}
                  onValueChange={(value) => updateSetting('ui', 'language', value)}
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="notifications">Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable desktop notifications
                  </p>
                </div>
                <Switch
                  id="notifications"
                  checked={settings.ui.notifications}
                  onCheckedChange={(checked) => updateSetting('ui', 'notifications', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="keyboard_shortcuts">Keyboard Shortcuts</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable keyboard shortcuts (Ctrl+G, Ctrl+V, etc.)
                  </p>
                </div>
                <Switch
                  id="keyboard_shortcuts"
                  checked={settings.ui.keyboard_shortcuts}
                  onCheckedChange={(checked) => updateSetting('ui', 'keyboard_shortcuts', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
