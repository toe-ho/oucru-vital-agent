'use client';

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { get, put } from "@/lib/api-client";
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
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
            ← Dashboard
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Settings</h1>
        </div>

        {!isAdmin && (
          <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
            You have read-only access. Contact an administrator to modify thresholds.
          </div>
        )}

        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-sm font-semibold text-gray-800">SQI Thresholds</h2>

          {isLoading ? (
            <p className="text-sm text-gray-500">Loading…</p>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              {Object.keys(settings).length === 0 ? (
                <p className="text-sm text-gray-500">No threshold settings found.</p>
              ) : (
                Object.entries(settings).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-gray-700">
                      {key.replace(/_/g, " ")}
                    </label>
                    <input
                      type="text"
                      value={String(value)}
                      onChange={(e) => handleChange(key, e.target.value)}
                      disabled={!isAdmin}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>
                ))
              )}

              {saveError && (
                <p className="text-sm text-red-600">{saveError}</p>
              )}
              {saveSuccess && (
                <p className="text-sm text-green-600">Settings saved successfully.</p>
              )}

              {isAdmin && Object.keys(settings).length > 0 && (
                <button
                  type="submit"
                  disabled={isSaving}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSaving ? "Saving…" : "Save Changes"}
                </button>
              )}
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
