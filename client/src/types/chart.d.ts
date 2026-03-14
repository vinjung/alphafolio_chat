// client/src/types/chart.d.ts

/**
 * Dataset for line/bar charts
 */
export interface ChartDataset {
  label: string;
  data: (number | null)[];
  borderColor?: string;
  backgroundColor?: string;
  tension?: number;
}

/**
 * Line chart visualization data
 */
export interface LineChartVisualizationData {
  type: 'line_chart';
  title: string;
  data: {
    labels: string[];
    datasets: ChartDataset[];
  };
  options?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
    yAxisMin?: number;
    yAxisMax?: number;
    yAxisTicks?: Record<string, string>;
    isQuantGrade?: boolean;
  };
}

/**
 * Bar chart visualization data
 */
export interface BarChartVisualizationData {
  type: 'bar_chart';
  title: string;
  data: {
    labels: string[];
    datasets: {
      label: string;
      data: (number | null)[];
      backgroundColor: string[];
    }[];
  };
  options?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
  };
}

/**
 * Candlestick chart visualization data
 */
export interface CandlestickVisualizationData {
  type: 'candlestick';
  title: string;
  data: {
    labels: string[];
    datasets: {
      data: {
        open: number | null;
        high: number | null;
        low: number | null;
        close: number | null;
      }[];
    }[];
  };
  options?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
  };
}

/**
 * Pie chart visualization data
 */
export interface PieChartVisualizationData {
  type: 'pie_chart';
  title: string;
  data: {
    labels: string[];
    datasets: {
      data: (number | null)[];
      backgroundColor: string[];
    }[];
  };
  options?: {
    showPercentage?: boolean;
  };
}

/**
 * Table visualization data
 */
export interface TableVisualizationData {
  type: 'table';
  title: string;
  data: {
    headers: string[];
    rows: (string | number | null)[][];
    total_count: number;
    displayed_count: number;
  };
  options?: {
    sortable?: boolean;
    pagination?: boolean;
  };
}

/**
 * Multi chart visualization data (indicator selector UI)
 */
export interface MultiChartVisualizationData {
  type: 'multi_chart';
  title: string;
  charts: {
    label: string;
    visualization: LineChartVisualizationData;
  }[];
  defaultIndex?: number;
}

/**
 * Union of all visualization data types
 */
export type VisualizationData =
  | TableVisualizationData
  | LineChartVisualizationData
  | CandlestickVisualizationData
  | BarChartVisualizationData
  | PieChartVisualizationData
  | MultiChartVisualizationData;
