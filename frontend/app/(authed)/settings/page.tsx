'use client';

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { get, put } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingState } from "@/components/feedback/loading-state";
import type { ThresholdSettings } from "@/lib/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [settings, setSettings] = useState<ThresholdSettings>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    get<ThresholdSettings>("/api/settings/thresholds")
      .then((data) => setSettings(data))
      .catch(() => setSettings({}))
      .finally(() => setIsLoading(false));
  }, []);

  const handleChange = (key: string, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaveSuccess(false);
    setSaveError(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await put<ThresholdSettings>("/api/settings/thresholds", settings);
      setSaveSuccess(true);
    } catch (err) {
      setSaveError((err as Error).message ?? "Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-xl font-bold text-foreground">Settings</h1>

      {!isAdmin && (
        <div className="rounded-md border border-uncomputable/30 bg-uncomputable/10 px-4 py-3 text-sm text-uncomputable">
          You have read-only access. Contact an administrator to modify thresholds.
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">SQI Thresholds</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <LoadingState rows={4} />
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              {Object.keys(settings).length === 0 ? (
                <p className="text-sm text-muted-foreground">No threshold settings found.</p>
              ) : (
                Object.entries(settings).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-foreground mb-1">
                      {key.replace(/_/g, " ")}
                    </label>
                    <Input
                      type="text"
                      value={String(value)}
                      onChange={(e) => handleChange(key, e.target.value)}
                      disabled={!isAdmin}
                    />
                  </div>
                ))
              )}

              {saveError && <p className="text-sm text-reject">{saveError}</p>}
              {saveSuccess && <p className="text-sm text-accept">Settings saved successfully.</p>}

              {isAdmin && Object.keys(settings).length > 0 && (
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving…" : "Save Changes"}
                </Button>
              )}
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
