"use client";

import { useState } from "react";
import { Zap, AlertTriangle, Target, Lightbulb, Loader2 } from "lucide-react";
import api from "@/lib/api";
import useSWR from "swr";
import { motion } from "framer-motion";

export function AIAnalysisCard({ userId }: { userId?: string }) {
  const [data, setData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const generateAnalysis = async () => {
    if (!userId) return;
    setIsGenerating(true);
    try {
      const res = await api.post(`/ai/analyze/${userId}`);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const IconMap: Record<string, React.ElementType> = {
    strengths: Target,
    weaknesses: AlertTriangle,
    recommendations: Lightbulb,
  };

  const ColorMap: Record<string, string> = {
    strengths: "text-success bg-success/10",
    weaknesses: "text-danger bg-danger/10",
    recommendations: "text-primary bg-primary/10",
  };

  return (
    <div className="glass-card p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="section-title flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary" />
          AI Analysis & Insights
        </h2>
        <button
          onClick={generateAnalysis}
          disabled={isGenerating}
          className="btn-ghost text-xs"
        >
          {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Refresh"}
        </button>
      </div>

      {!data ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <p className="text-dark-muted mb-4">No AI analysis available yet.</p>
          <button onClick={generateAnalysis} className="btn-primary">
            Generate Insights
          </button>
        </div>
      ) : (
        <div className="space-y-6 flex-1">
          <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
            <p className="text-sm text-dark-text leading-relaxed">
              {data.summary}
            </p>
          </div>

          <div className="grid gap-4">
            {["strengths", "weaknesses", "recommendations"].map((category, idx) => {
              const Icon = IconMap[category];
              const items = data[category] || [];
              if (items.length === 0) return null;

              return (
                <motion.div
                  key={category}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`w-4 h-4 ${ColorMap[category].split(" ")[0]}`} />
                    <h3 className="text-sm font-semibold capitalize text-dark-text">
                      {category}
                    </h3>
                  </div>
                  <ul className="space-y-2 pl-6">
                    {items.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-dark-muted list-disc marker:text-dark-border">
                        {item}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
