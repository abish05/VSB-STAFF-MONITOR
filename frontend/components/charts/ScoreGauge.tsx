"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

export function ScoreGauge({ value, size = 120, label }: { value: number; size?: number; label?: string }) {
  const data = [
    { name: "Score", value: value },
    { name: "Remaining", value: 100 - value },
  ];

  const getColor = (v: number) => {
    if (v >= 80) return "#22C55E";
    if (v >= 60) return "#3B82F6";
    if (v >= 40) return "#F59E0B";
    return "#EF4444";
  };

  return (
    <div className="flex flex-col items-center justify-center relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius="75%"
            outerRadius="100%"
            startAngle={225}
            endAngle={-45}
            dataKey="value"
            stroke="none"
          >
            <Cell fill={getColor(value)} />
            <Cell fill="#334155" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-xl font-display font-bold text-dark-text">{value.toFixed(0)}</span>
      </div>
      {label && <p className="absolute -bottom-4 text-xs font-medium text-dark-muted whitespace-nowrap">{label}</p>}
    </div>
  );
}
