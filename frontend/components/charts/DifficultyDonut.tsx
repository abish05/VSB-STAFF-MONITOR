"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

export function DifficultyDonut({ easy, medium, hard }: { easy: number; medium: number; hard: number }) {
  const data = [
    { name: "Easy", value: easy, color: "#22C55E" },
    { name: "Medium", value: medium, color: "#F59E0B" },
    { name: "Hard", value: hard, color: "#EF4444" },
  ];

  if (easy === 0 && medium === 0 && hard === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-dark-muted text-sm">
        No problems solved yet
      </div>
    );
  }

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="80%"
            paddingAngle={5}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: "#1E293B", border: "1px solid #334155", borderRadius: "8px" }}
            itemStyle={{ color: "#E2E8F0" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
