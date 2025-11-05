"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

type ChartDatum = {
  timestamp: string;
  [key: string]: string | number;
};

interface MetricsChartProps {
  title: string;
  data: ChartDatum[];
  dataKeys: { key: string; color: string; label: string }[];
  type?: "line" | "area" | "bar";
  height?: number;
}

export function MetricsChart({
  title,
  data,
  dataKeys,
  type = "line",
  height = 300,
}: MetricsChartProps) {
  const ChartComponent =
    type === "area" ? AreaChart : type === "bar" ? BarChart : LineChart;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
              }}
            />
            <Legend />

            {dataKeys.map((item) => {
              if (type === "area") {
                return (
                  <Area
                    key={item.key}
                    type="monotone"
                    dataKey={item.key}
                    stroke={item.color}
                    fill={item.color}
                    fillOpacity={0.2}
                    name={item.label}
                  />
                );
              } else if (type === "bar") {
                return (
                  <Bar
                    key={item.key}
                    dataKey={item.key}
                    fill={item.color}
                    name={item.label}
                  />
                );
              } else {
                return (
                  <Line
                    key={item.key}
                    type="monotone"
                    dataKey={item.key}
                    stroke={item.color}
                    strokeWidth={2}
                    name={item.label}
                  />
                );
              }
            })}
          </ChartComponent>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
