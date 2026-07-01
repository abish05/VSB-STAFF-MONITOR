"use client";

import { Trophy, Award, Lock } from "lucide-react";
import { motion } from "framer-motion";

export interface Achievement {
  id: string;
  code: string;
  name: string;
  description: string;
  icon: string;
  is_earned: boolean;
  earned_at?: string;
}

export function AchievementsPanel({ achievements }: { achievements: Achievement[] }) {
  const earnedCount = achievements.filter((a) => a.is_earned).length;

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="section-title flex items-center gap-2">
          <Trophy className="w-5 h-5 text-warning" />
          Achievements
        </h2>
        <span className="stat-badge bg-warning/20 text-warning border border-warning/30">
          {earnedCount} / {achievements.length} Unlocked
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1 content-start overflow-y-auto pr-2">
        {achievements.map((a, idx) => (
          <motion.div
            key={a.code}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.05 }}
            className={`p-3 rounded-xl border flex items-center gap-3 transition-all ${
              a.is_earned
                ? "bg-dark-card border-warning/30 hover:border-warning/50"
                : "bg-dark-bg/50 border-dark-border opacity-60 grayscale"
            }`}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
              a.is_earned ? "bg-warning/20 text-2xl" : "bg-dark-border text-dark-muted"
            }`}>
              {a.is_earned ? a.icon : <Lock className="w-4 h-4" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-semibold truncate ${a.is_earned ? "text-dark-text" : "text-dark-muted"}`}>
                {a.name}
              </p>
              <p className="text-xs text-dark-muted truncate" title={a.description}>
                {a.description}
              </p>
            </div>
            {a.is_earned && (
              <Award className="w-4 h-4 text-warning shrink-0" />
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
