'use client';

import { useState } from 'react';
import { LineChart } from './line-chart';
import type { MultiChartVisualizationData } from '@/types/chart';

interface MultiChartProps {
  data: MultiChartVisualizationData;
  height?: number;
}

export function MultiChart({ data, height = 250 }: MultiChartProps) {
  const [selectedIndex, setSelectedIndex] = useState(data.defaultIndex ?? 0);
  const { charts } = data;

  if (!charts || charts.length === 0) {
    return (
      <div className="text-neutral-500 text-sm py-4 text-center">
        데이터가 없습니다.
      </div>
    );
  }

  const selectedChart = charts[selectedIndex];

  return (
    <div className="w-full">
      {/* Indicator selector buttons */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {charts.map((chart, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedIndex(idx)}
            className={`px-3 py-1.5 text-xs rounded-full border transition-colors
              ${
                idx === selectedIndex
                  ? 'bg-neutral-900 text-white border-neutral-900'
                  : 'bg-white text-neutral-600 border-neutral-200 hover:border-neutral-400'
              }`}
          >
            {chart.label}
          </button>
        ))}
      </div>

      {/* Selected chart */}
      <LineChart data={selectedChart.visualization} height={height} />
    </div>
  );
}
