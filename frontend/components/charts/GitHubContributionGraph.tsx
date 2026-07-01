"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export function GitHubContributionGraph({ data }: { data: Array<{ date: string; count: number }> | undefined }) {
  // Use mock data if no real data is provided yet
  const chartData = data?.length ? data : Array.from({ length: 30 }, (_, i) => ({
    date: `2025-01-${i + 1}`,
    count: Math.floor(Math.random() * 10),
  }));

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#22C55E" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
          <XAxis dataKey="date" tick={{ fill: "#94A3B8", fontSize: 10 }} tickLine={false} axisLine={false} minTickGap={30} />
          <YAxis tick={{ fill: "#94A3B8", fontSize: 10 }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1E293B", border: "1px solid #334155", borderRadius: "8px" }}
            itemStyle={{ color: "#E2E8F0" }}
          />
          <Area type="monotone" dataKey="count" stroke="#22C55E" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
