"use client";

import { useMemo } from "react";

interface HeatmapDay {
  date: string;
  count: number;
  level: number;
}

export function LeetCodeHeatmap({ data }: { data: HeatmapDay[] | undefined }) {
  const weeks = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return Array.from({ length: 52 }, () =>
        Array.from({ length: 7 }, () => ({ count: 0, level: 0, date: "" }))
      );
    }

    const weeksArr: Array<Array<{ count: number; level: number; date: string }>> = [];
    let currentWeek: Array<{ count: number; level: number; date: string }> = [];

    // Find the day of week of the first date to align it (Sunday=0, Saturday=6)
    const firstDate = new Date(data[0].date);
    const firstDayOfWeek = isNaN(firstDate.getTime()) ? 0 : firstDate.getDay();

    // Pad the first week with empty cells
    for (let i = 0; i < firstDayOfWeek; i++) {
      currentWeek.push({ count: 0, level: 0, date: "" });
    }

    for (const item of data) {
      currentWeek.push({
        count: item.count ?? 0,
        level: item.level ?? 0,
        date: item.date ?? ""
      });

      if (currentWeek.length === 7) {
        weeksArr.push(currentWeek);
        currentWeek = [];
      }
    }

    if (currentWeek.length > 0) {
      // Pad the last week to 7 days
      while (currentWeek.length < 7) {
        currentWeek.push({ count: 0, level: 0, date: "" });
      }
      weeksArr.push(currentWeek);
    }

    // Keep up to 53 weeks to fit full year
    return weeksArr.slice(-53);
  }, [data]);

  const getColor = (level: number) => {
    if (level === 0) return "bg-dark-border/40 hover:bg-dark-border/80";
    if (level === 1) return "bg-emerald-500/20 hover:bg-emerald-500/40";
    if (level === 2) return "bg-emerald-500/45 hover:bg-emerald-500/65";
    if (level === 3) return "bg-emerald-500/70 hover:bg-emerald-500/90";
    return "bg-emerald-500 hover:bg-emerald-400";
  };

  return (
    <div className="w-full overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-dark-border">
      <div className="flex gap-[3px] min-w-max">
        {weeks.map((week, wIdx) => (
          <div key={wIdx} className="flex flex-col gap-[3px]">
            {week.map((day, dIdx) => (
              <div
                key={dIdx}
                className={`w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] rounded-[1.5px] transition-colors duration-200 cursor-pointer ${
                  day.date ? getColor(day.level) : "opacity-0 pointer-events-none"
                }`}
                title={
                  day.date
                    ? `${day.count} submission${day.count !== 1 ? "s" : ""} on ${new Date(
                        day.date
                      ).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}`
                    : ""
                }
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
