"use client";

import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
} from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Settings as SettingsIcon,
  Bell,
  Shield,
  Database,
  Cloud,
} from "lucide-react";
import type { CloudProvider, ProviderStatus } from "@/lib/types";

const statusColors: Record<ProviderStatus, string> = {
  connected: "text-green-600",
  configured: "text-blue-600",
  not_configured: "text-yellow-600",
  error: "text-red-600",
};

const statusLabels: Record<ProviderStatus, string> = {
  connected: "Connected",
  configured: "Configured",
  not_configured: "Not Configured",
  error: "Error",
};

const formatLastSync = (isoTimestamp?: string | null) => {
  if (!isoTimestamp) {
    return "Never";
  }

  const parsed = new Date(isoTimestamp);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown";
  }

  return parsed.toLocaleString();
};

export default function SettingsPage() {
  const [providers, setProviders] = useState<CloudProvider[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadProviders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/cloud-providers", {
        cache: "no-store",
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          (data as { error?: string; detail?: string })?.error ||
            (data as { error?: string; detail?: string })?.detail ||
            "Failed to load providers.",
        );
      }
      setProviders((data as { providers?: CloudProvider[] })?.providers ?? []);
    } catch (err) {
      console.error("Failed to load providers:", err);
      setProviders([]);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load providers."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  const handleConfigureClick = (providerId: string) => {
    setError(null);
    setSuccessMessage(null);
    if (activeProvider === providerId) {
      setActiveProvider(null);
      setFormValues({});
    } else {
      setActiveProvider(providerId);
      setFormValues({});
    }
  };

  const handleFieldChange = (field: string, value: string) => {
    setFormValues((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleConfigureSubmit = async (
    event: FormEvent<HTMLFormElement>,
    provider: CloudProvider,
  ) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const sanitizedCredentials = Object.entries(formValues).reduce<Record<string, string>>(
        (acc, [key, value]) => {
          const trimmed = value.trim();
          if (trimmed.length > 0) {
            acc[key] = trimmed;
          }
          return acc;
        },
        {},
      );

      const payload = {
        provider: provider.provider,
        credential_name: `${provider.display_name} Credential`,
        credentials: sanitizedCredentials,
        credential_type: "api_key",
        permissions: "read_only",
      };

      const response = await fetch("/api/cloud-providers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          (data as { detail?: string; error?: string; message?: string }).detail ||
            (data as { detail?: string; error?: string; message?: string }).error ||
            (data as { detail?: string; error?: string; message?: string }).message ||
            "Failed to save provider configuration.",
        );
      }

      setSuccessMessage(`Saved credentials for ${provider.display_name}.`);
      setActiveProvider(null);
      setFormValues({});
      await loadProviders();
    } catch (err) {
      console.error("Failed to save provider configuration:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to save provider configuration."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-gray-500">
          Configure your OptiInfra portal preferences
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <SettingsIcon className="h-5 w-5 text-primary-600" />
              <CardTitle>General Settings</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Portal Name
              </label>
              <input
                type="text"
                defaultValue="OptiInfra Portal"
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                defaultValue="30"
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary-600" />
              <CardTitle>Notifications</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Email Notifications</span>
              <input type="checkbox" defaultChecked className="h-4 w-4" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Slack Notifications</span>
              <input type="checkbox" className="h-4 w-4" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Alert Threshold</span>
              <select className="rounded-md border border-gray-300 px-3 py-1">
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary-600" />
              <CardTitle>Security</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                API Key
              </label>
              <input
                type="password"
                defaultValue="sk-xxxxxxxxxxxxxxxx"
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Two-Factor Auth</span>
              <input type="checkbox" className="h-4 w-4" />
            </div>
            <Button>Update Security</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary-600" />
              <CardTitle>Data &amp; Storage</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Data Retention (days)
              </label>
              <input
                type="number"
                defaultValue="90"
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Auto Backup</span>
              <input type="checkbox" defaultChecked className="h-4 w-4" />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-primary-600" />
              <CardTitle>Cloud Providers</CardTitle>
            </div>
            <Button size="sm" variant="outline" disabled>
              Add Provider
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                {successMessage}
              </div>
            )}

            <p className="text-sm text-gray-600">
              Configure API keys and Prometheus endpoints for your cloud providers.
              The Generic Collector now supports 12+ providers with a single workflow.
            </p>

            <div className="grid grid-cols-5 gap-4 border-b pb-2 text-sm font-medium text-gray-700">
              <span>Provider</span>
              <span>Type</span>
              <span>Status</span>
              <span>Last Sync</span>
              <span>Actions</span>
            </div>

            {loading ? (
              <div className="py-6 text-sm text-gray-500">Loading providers…</div>
            ) : providers.length === 0 ? (
              <div className="py-6 text-sm text-gray-500">
                No providers available yet. Configure the data-collector service to enable providers.
              </div>
            ) : (
              providers.map((provider) => (
                <div key={provider.provider} className="space-y-2 border-b pb-3">
                  <div className="grid grid-cols-5 gap-4 items-center">
                    <span className="text-sm font-medium">
                      {provider.display_name}
                    </span>
                    <span className="text-sm text-gray-600">
                      {provider.type === "generic" ? "Generic" : "Dedicated"}
                    </span>
                    <span
                      className={`text-sm ${statusColors[provider.status] ?? "text-gray-600"}`}
                    >
                      {statusLabels[provider.status] ?? provider.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatLastSync(provider.last_sync)}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleConfigureClick(provider.provider)}
                      disabled={submitting && activeProvider === provider.provider}
                    >
                      {activeProvider === provider.provider
                        ? "Close"
                        : provider.configured
                        ? "Manage"
                        : "Configure"}
                    </Button>
                  </div>

                  {activeProvider === provider.provider && (
                    <form
                      className="rounded-md border border-gray-200 bg-gray-50 p-4"
                      onSubmit={(event) =>
                        handleConfigureSubmit(event, provider)
                      }
                    >
                      {provider.requirements.length === 0 ? (
                        <p className="text-sm text-gray-600">
                          This provider does not require credential setup.
                        </p>
                      ) : (
                        <div className="grid gap-4 md:grid-cols-2">
                          {provider.requirements.map((requirement) => (
                            <div key={requirement.field} className="space-y-1">
                              <label className="text-sm font-medium text-gray-700">
                                {requirement.label}
                                {requirement.required && (
                                  <span className="ml-1 text-red-500">*</span>
                                )}
                              </label>
                              <input
                                type="text"
                                required={requirement.required}
                                value={formValues[requirement.field] || ""}
                                onChange={(event) =>
                                  handleFieldChange(
                                    requirement.field,
                                    event.target.value
                                  )
                                }
                                placeholder={requirement.label}
                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                              />
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="mt-4 flex gap-2">
                        <Button size="sm" type="submit" disabled={submitting}>
                          {submitting ? "Saving..." : "Save Configuration"}
                        </Button>
                        <Button
                          size="sm"
                          type="button"
                          variant="outline"
                          onClick={() => handleConfigureClick(provider.provider)}
                          disabled={submitting}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  )}
                </div>
              ))
            )}

            <div className="rounded-lg bg-blue-50 p-4">
              <p className="text-sm text-blue-800">
                <strong>Phase 6.6 Generic Collector:</strong> Configure a Prometheus URL and optional API key to onboard new providers in minutes.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Agent Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4 border-b pb-2 text-sm font-medium text-gray-700">
              <span>Agent</span>
              <span>Status</span>
              <span>Port</span>
              <span>Actions</span>
            </div>
            {[
              { name: "Cost Agent", port: 8001 },
              { name: "Performance Agent", port: 8002 },
              { name: "Resource Agent", port: 8003 },
              { name: "Application Agent", port: 8004 },
            ].map((agent) => (
              <div key={agent.name} className="grid grid-cols-4 items-center gap-4">
                <span className="text-sm">{agent.name}</span>
                <span className="text-sm text-green-600">Active</span>
                <span className="text-sm text-gray-600">{agent.port}</span>
                <Button size="sm" variant="outline">
                  Configure
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
