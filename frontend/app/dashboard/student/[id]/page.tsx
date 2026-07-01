"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import useSWR from "swr";
import { motion } from "framer-motion";
import { ArrowLeft, Download, Loader2, Code2, GitBranch, Trophy, Flame, ExternalLink } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { ScoreGauge } from "@/components/charts/ScoreGauge";
import { AIAnalysisCard } from "@/components/cards/AIAnalysisCard";
import toast from "react-hot-toast";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function StudentDetailView() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: dashboard, isLoading } = useSWR(`/staff/mentees/${studentId}`, fetcher);

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      const response = await api.get(`/reports/pdf/${studentId}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `codepulse_report_${dashboard?.user?.full_name?.replace(" ", "_") || studentId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF report downloaded!");
    } catch (error) {
      toast.error("Failed to generate PDF report");
    } finally {
      setIsDownloading(false);
    }
  };

  const role = user?.role?.name as "student" | "staff" | "admin" || "staff";
  
  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden bg-dark-bg">
        <Sidebar role={role} />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
      </div>
    );
  }

  const student = dashboard?.student;
  const perf = dashboard?.performance;
  const lc = dashboard?.leetcode;
  const gh = dashboard?.github;

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role={role} />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={() => router.back()} className="btn-ghost p-2">
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-display font-bold text-dark-text">{student?.full_name}</h1>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                    student?.is_active 
                      ? "bg-green-100 text-green-800" 
                      : "bg-red-100 text-red-800"
                  }`}>
                    {student?.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <p className="text-dark-muted text-sm">{student?.email}</p>
              </div>
            </div>
            <button onClick={handleDownloadPdf} disabled={isDownloading} className="btn-secondary">
              {isDownloading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
              Download PDF Report
            </button>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Main Stats Column */}
            <div className="lg:col-span-2 space-y-6">
              
              <div className="glass-card p-6 flex flex-col sm:flex-row items-center gap-6 justify-around">
                <div className="text-center">
                  <p className="text-4xl font-display font-black gradient-text">{perf?.total_score?.toFixed(1) || 0}</p>
                  <p className="text-dark-text font-semibold mt-1">Overall Score</p>
                  <span className={`mt-2 ${perf?.classification === "Excellent" ? "badge-excellent" : "badge-average"}`}>
                    {perf?.classification || "Unknown"}
                  </span>
                </div>
                <ScoreGauge value={perf?.placement_score || 0} size={120} label="Placement Readiness" />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* LeetCode sector */}
                <div className="glass-card p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-dark-border pb-3">
                    <div className="flex items-center gap-2">
                      <Code2 className="w-5 h-5 text-primary" />
                      <span className="text-base font-bold text-dark-text">LeetCode Tracker</span>
                    </div>
                    {lc?.current_streak > 0 && (
                      <span className="flex items-center gap-1 text-xs text-orange-600 bg-orange-100 px-2 py-0.5 rounded-full font-bold">
                        <Flame className="w-3.5 h-3.5 fill-current" /> {lc.current_streak} days
                      </span>
                    )}
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-3xl font-black text-dark-text">
                        {lc?.total_solved || 0}{" "}
                        <span className="text-xs font-semibold text-dark-muted">solved total</span>
                      </p>
                      <div className="flex gap-2 text-xs mt-1 font-semibold">
                        <span className="text-green-600 bg-green-50 px-2 py-0.5 rounded">E: {lc?.easy || 0}</span>
                        <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded">M: {lc?.medium || 0}</span>
                        <span className="text-red-600 bg-red-50 px-2 py-0.5 rounded">H: {lc?.hard || 0}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-2 text-xs border-t border-dark-border/40">
                      <div>
                        <p className="text-dark-muted font-medium">Solved Today</p>
                        <p className="text-lg font-bold text-dark-text mt-0.5">{lc?.solved_today || 0} problems</p>
                      </div>
                      <div>
                        <p className="text-dark-muted font-medium">Contests Won/Attended</p>
                        <p className="text-lg font-bold text-dark-text mt-0.5 flex items-center gap-1">
                          <Trophy className="w-4 h-4 text-yellow-600" />
                          {lc?.contests_attended || 0} ({Math.round(lc?.contest_rating || 0)})
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* GitHub sector */}
                <div className="glass-card p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-dark-border pb-3">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-5 h-5 text-success" />
                      <span className="text-base font-bold text-dark-text">GitHub Tracker</span>
                    </div>
                    {student?.github_username && (
                      <a
                        href={`https://github.com/${student.github_username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-xs text-primary hover:underline font-semibold"
                      >
                        Profile <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="text-3xl font-black text-dark-text">
                        {gh?.total_commits || 0}{" "}
                        <span className="text-xs font-semibold text-dark-muted">commits total</span>
                      </p>
                      <p className="text-xs text-dark-muted mt-1 font-medium">
                        Active repositories: <span className="text-dark-text font-semibold">{gh?.public_repos || 0} projects</span>
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-2 text-xs border-t border-dark-border/40">
                      <div>
                        <p className="text-dark-muted font-medium">Commits Today</p>
                        <p className="text-lg font-bold text-dark-text mt-0.5">{gh?.commits_today || 0} commits</p>
                      </div>
                      <div>
                        <p className="text-dark-muted font-medium">PRs Submitted</p>
                        <p className="text-lg font-bold text-dark-text mt-0.5">{gh?.pull_requests || 0} pull requests</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Analysis Column */}
            <div className="lg:col-span-1">
              <AIAnalysisCard userId={studentId} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
