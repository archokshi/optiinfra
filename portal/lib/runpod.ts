import type {
  DashboardData,
  RunPodDashboardPlaceholder,
  RunPodDashboardSection,
} from "./types";

export const formatCurrency = (value?: number | null, currency: string = "USD") => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatNumber = (value?: number | null, options: Intl.NumberFormatOptions = {}) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }
  return new Intl.NumberFormat(undefined, options).format(value);
};

export const formatDateTime = (
  value?: string | null,
  options: Intl.DateTimeFormatOptions = { dateStyle: "medium", timeStyle: "short" },
) => {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, options);
};

export const formatKey = (key: string) =>
  key
    .replace(/([A-Z])/g, " $1")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^./, (char) => char.toUpperCase());

export const formatDetailValue = (value: unknown) => {
  if (typeof value === "number") {
    return formatNumber(value, { maximumFractionDigits: 2 });
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
};

export const isRunPodDashboardSection = (
  value: DashboardData["metrics"]["runpod"] | undefined,
): value is RunPodDashboardSection => {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as RunPodDashboardSection;
  return (
    Array.isArray(candidate.billing) &&
    Array.isArray(candidate.endpoint_health) &&
    Array.isArray(candidate.pods)
  );
};

export const asRunPodPlaceholder = (
  value: DashboardData["metrics"]["runpod"] | undefined,
): RunPodDashboardPlaceholder | null => {
  if (!value || typeof value !== "object") {
    return null;
  }
  if ("billing" in value || "pods" in value || "endpoint_health" in value) {
    return null;
  }
  return value as RunPodDashboardPlaceholder;
};
