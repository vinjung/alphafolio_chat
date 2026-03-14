'use client';

import { LineChart } from './line-chart';
import { MultiChart } from './multi-chart';
import type { VisualizationData } from '@/types/chart';
import type {
  LineChartVisualizationData,
  MultiChartVisualizationData,
} from '@/types/chart';

interface ChartRendererProps {
  visualization: VisualizationData;
}

export function ChartRenderer({ visualization }: ChartRendererProps) {
  switch (visualization.type) {
    case 'line_chart':
      return (
        <LineChart data={visualization as LineChartVisualizationData} />
      );
    case 'multi_chart':
      return (
        <MultiChart data={visualization as MultiChartVisualizationData} />
      );
    // table, bar_chart, candlestick, pie_chart can be added here
    default:
      return null;
  }
}
