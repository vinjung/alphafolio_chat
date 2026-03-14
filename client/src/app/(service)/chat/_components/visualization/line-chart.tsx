'use client';

import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import type { LineChartVisualizationData } from '@/types/chart';

interface LineChartProps {
  data: LineChartVisualizationData;
  height?: number;
}

export function LineChart({ data, height = 250 }: LineChartProps) {
  const { data: chartData, options } = data;

  if (!chartData?.labels || !chartData?.datasets?.length) {
    return (
      <div className="text-neutral-500 text-sm py-4 text-center">
        데이터가 없습니다.
      </div>
    );
  }

  // Transform backend format to recharts format
  // Backend: { labels: [...], datasets: [{ label, data, borderColor }] }
  // Recharts: [{ name: label, series1: val, series2: val }, ...]
  const rechartsData = chartData.labels.map((label, idx) => {
    const point: Record<string, string | number | null> = { name: label };
    chartData.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[idx] ?? null;
    });
    return point;
  });

  // Custom Y-axis tick formatter for quant grade charts
  const yTickFormatter = options?.yAxisTicks
    ? (value: number) => options.yAxisTicks?.[String(value)] ?? String(value)
    : undefined;

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={rechartsData}
          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            width={50}
            domain={
              options?.yAxisMin !== undefined && options?.yAxisMax !== undefined
                ? [options.yAxisMin, options.yAxisMax]
                : ['auto', 'auto']
            }
            tickFormatter={yTickFormatter}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: '1px solid #e5e7eb',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            }}
          />
          {chartData.datasets.map((dataset, idx) => (
            <Line
              key={idx}
              type="monotone"
              dataKey={dataset.label}
              stroke={dataset.borderColor || '#3b82f6'}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3 }}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}
