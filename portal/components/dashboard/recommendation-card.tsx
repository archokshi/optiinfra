"use client";

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import type { Recommendation } from "@/lib/types";
import { formatCurrency, formatPercentage, formatDateTime } from "@/lib/utils";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const riskIcons = {
  low: CheckCircle,
  medium: AlertTriangle,
  high: XCircle,
};

const riskColors = {
  low: "text-green-600",
  medium: "text-yellow-600",
  high: "text-red-600",
};

export function RecommendationCard({
  recommendation,
  onApprove,
  onReject,
}: RecommendationCardProps) {
  const RiskIcon = riskIcons[recommendation.risk_level];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{recommendation.title}</CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              {recommendation.description}
            </p>
          </div>
          <Badge
            variant={
              recommendation.status === "pending"
                ? "info"
                : recommendation.status === "approved"
                ? "success"
                : recommendation.status === "rejected"
                ? "error"
                : "default"
            }
          >
            {recommendation.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {recommendation.estimated_savings && (
            <div>
              <p className="text-xs text-gray-500">Estimated Savings</p>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(recommendation.estimated_savings)}
              </p>
            </div>
          )}

          {recommendation.estimated_improvement && (
            <div>
              <p className="text-xs text-gray-500">Estimated Improvement</p>
              <p className="text-lg font-semibold text-blue-600">
                {formatPercentage(recommendation.estimated_improvement)}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mt-4">
          <RiskIcon className={`h-4 w-4 ${riskColors[recommendation.risk_level]}`} />
          <span className="text-sm text-gray-600">
            {recommendation.risk_level.charAt(0).toUpperCase() +
              recommendation.risk_level.slice(1)}{" "}
            Risk
          </span>
        </div>

        <p className="text-xs text-gray-400 mt-4">
          Created: {formatDateTime(recommendation.created_at)}
        </p>
      </CardContent>

      {recommendation.status === "pending" && onApprove && onReject && (
        <CardFooter className="flex gap-2">
          <Button
            size="sm"
            onClick={() => onApprove(recommendation.id)}
            className="flex-1"
          >
            Approve
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onReject(recommendation.id)}
            className="flex-1"
          >
            Reject
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
