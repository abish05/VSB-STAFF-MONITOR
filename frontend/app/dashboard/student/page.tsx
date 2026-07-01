"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import useSWR from "swr";
import {
  Code2, GitBranch, Bell, RefreshCw, Search, ShoppingCart, User as UserIcon,
  ChevronDown, ArrowRight, BookMarked, MessageSquare, Grid, Trophy, Award, Building,
} from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { LeetCodeHeatmap } from "@/components/charts/LeetCodeHeatmap";
import { GitHubContributionGraph } from "@/components/charts/GitHubContributionGraph";
import { AIAnalysisCard } from "@/components/cards/AIAnalysisCard";
import { AchievementsPanel } from "@/components/cards/AchievementsPanel";
import toast from "react-hot-toast";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

function StudentDashboardContent() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentTab = searchParams ? searchParams.get("tab") || "skill" : "skill";
  const [isSyncing, setIsSyncing] = useState(false);
  const [leaderboardMetric, setLeaderboardMetric] = useState("overall");

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: dashboard, mutate: mutateDashboard } = useSWR("/student/dashboard", fetcher);
  const { data: leetcode, mutate: mutateLeetCode } = useSWR("/student/leetcode", fetcher);
  const { data: github, mutate: mutateGitHub } = useSWR("/student/github", fetcher);
  const { data: achievements } = useSWR("/achievements", fetcher);
  const { data: leaderboard } = useSWR(currentTab === "leaderboard" ? `/leaderboard/students?metric=${leaderboardMetric}` : null, fetcher);

  async function handleSync() {
    setIsSyncing(true);
    try {
      const res = await api.post("/student/sync");
      const lc = res.data?.leetcode;
      const gh = res.data?.github;
      if (lc?.status === "success") {
        toast.success(`✅ LeetCode synced! ${lc.total_solved} problems solved.`);
      } else if (lc?.status === "skipped") {
        toast(`⚠️ LeetCode: ${lc.reason}`, { icon: "⚠️" });
      }
      if (gh?.status === "success") {
        toast.success(`✅ GitHub synced! ${gh.commits} commits tracked.`);
      } else if (gh?.status === "skipped") {
        toast(`⚠️ GitHub: ${gh.reason}`, { icon: "⚠️" });
      }
      mutateDashboard();
      mutateLeetCode();
      mutateGitHub();
    } catch {
      toast.error("Sync failed. Please try again.");
    } finally {
      setIsSyncing(false);
    }
  }

  const perf = dashboard?.performance;
  const lc = dashboard?.leetcode;
  const gh = dashboard?.github;

  const currentYear = new Date().getFullYear();
  const studentYear = user?.year || dashboard?.profile?.year || 3;
  const batchYear = currentYear + (4 - studentYear);

  const lastSyncedRaw = leetcode?.stats?.last_synced || github?.stats?.last_synced;
  const lastUpdatedDate = lastSyncedRaw
    ? new Date(lastSyncedRaw).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      })
    : "29 Jun 2026, 04:45 PM";

  const handleTabChange = (tab: string) => {
    router.push(`/dashboard/student?tab=${tab}`);
  };

  const solvedCount = lc?.total_solved ?? leetcode?.stats?.total_solved ?? 0;
  const totalTarget = 500;
  const percentage = Math.min((solvedCount / totalTarget) * 100, 100);

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role="student" activeTab={currentTab} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-dark-card/50 border-b border-dark-border px-6 py-4 flex items-center justify-between sticky top-0 z-30 backdrop-blur-md">
          <div className="relative w-64 md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
            <input
              type="text"
              placeholder="Search"
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-dark-bg border border-dark-border text-sm text-dark-text placeholder-dark-muted focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all"
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-red-500 border border-dark-bg" />
            </button>

            <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all">
              <ShoppingCart className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 pl-2 border-l border-dark-border select-none">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">
                {user?.full_name?.[0]?.toUpperCase() || "A"}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-sm font-semibold text-white tracking-wide uppercase">
                  {user?.full_name?.toUpperCase() || "ABISH A"}
                </span>
                <span className="text-[10px] text-dark-muted tracking-wider uppercase font-medium">
                  {user?.role?.name || "Student"}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </div>
          </div>
        </header>

        <div className="bg-dark-bg border-b border-dark-border px-6 md:px-8 py-3 flex gap-2">
          {[
            { id: "skill", label: "Skill" },
            { id: "courses", label: "Course" },
            { id: "drives", label: "Drives" }
          ].map((tab) => {
            const isActive = currentTab === tab.id || (tab.id === "skill" && !["courses", "drives"].includes(currentTab));
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${
                  isActive
                    ? "bg-[#2563eb] text-white shadow-md"
                    : "text-slate-400 hover:text-white hover:bg-white/5 border border-dark-border"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <main className="flex-1 overflow-y-auto no-scrollbar">
          <AnimatePresence mode="wait">
            {(!["courses", "drives", "contest", "company-tests", "leaderboard", "engagement", "nerd"].includes(currentTab)) && (
              <motion.div
                key="skill-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
                      Dashboard
                    </h1>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="glass-card px-4 py-2 border border-dark-border text-xs text-dark-muted font-medium flex items-center gap-1.5 select-none">
                      <span>Last Updated on</span>
                      <span className="text-white font-semibold">{lastUpdatedDate}</span>
                    </div>

                    <button
                      onClick={handleSync}
                      disabled={isSyncing}
                      className="btn-secondary gap-2 disabled:opacity-60 py-2 cursor-pointer"
                    >
                      <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                      {isSyncing ? "Syncing..." : "Sync"}
                    </button>
                  </div>
                </div>

                <div className="glass-card overflow-hidden relative shadow-card hover:shadow-card-hover transition-all duration-300">
                  <div className="relative w-full h-40 md:h-48"
                       style={{ background: "linear-gradient(105deg, #3B0066 0%, #8E2DE2 30%, #F000FF 70%, #ff7675 100%)" }}>
                    <div className="absolute right-[20%] bottom-[-20px] w-24 h-24 rounded-full bg-gradient-to-t from-yellow-300 to-amber-500 opacity-60 filter blur-xs" />
                    <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle at 20% 50%, rgba(255,255,255,0.15) 0%, transparent 60%)" }} />
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.05)_1px,_transparent_1px)] bg-[size:16px_16px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" />
                  </div>

                  <div className="p-6 pt-16 md:pt-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative">
                    <div className="absolute left-6 -top-10 md:-top-12 w-20 h-20 md:w-24 md:h-24 rounded-full border-4 border-[#1e293b] bg-slate-200 flex items-center justify-center shadow-lg overflow-hidden select-none">
                      <UserIcon className="w-10 h-10 md:w-12 md:h-12 text-slate-400" />
                    </div>

                    <div className="md:pl-28 flex flex-col">
                      <h2 className="text-xl md:text-2xl font-bold text-white tracking-wide">
                        {user?.full_name || "ABISH A"}
                      </h2>
                      <p className="text-slate-400 text-sm font-medium mt-0.5">
                        {user?.email || "abishstk@gmail.com"}
                      </p>

                      <div className="flex flex-wrap gap-x-4 gap-y-2 mt-4 text-xs font-semibold text-slate-300">
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400">Register Number :</span>
                          <span className="text-white font-bold">{user?.reg_no || "723723104008"}</span>
                        </div>
                        <span className="hidden md:inline text-slate-500">|</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400">Degree :</span>
                          <span className="text-white font-bold">BE - {user?.department?.code || "CSE"}</span>
                        </div>
                        <span className="hidden md:inline text-slate-500">|</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400">Batch :</span>
                          <span className="text-white font-bold">{batchYear}</span>
                        </div>
                        <span className="hidden md:inline text-slate-500">|</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400">College :</span>
                          <span className="text-white font-bold">VSB College of Engineering & Technical Campus</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="glass-card p-5 flex flex-col justify-between h-44 hover:border-slate-600 transition-all select-none">
                    <div className="text-sm font-bold text-slate-300 tracking-wide uppercase">Neo-PAT</div>
                    <div className="bg-[#1e293b]/40 border border-slate-700/40 rounded-xl p-4 flex flex-col items-center justify-center mt-3">
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Your Score</span>
                      <span className="text-4xl font-extrabold text-[#2563eb] mt-0.5">
                        {perf?.placement_score ? Math.round(perf.placement_score * 4.5) : 371}
                      </span>
                    </div>
                  </div>

                  <div className="glass-card p-5 flex flex-col justify-between h-44 hover:border-slate-600 transition-all select-none">
                    <div className="text-sm font-bold text-slate-300 tracking-wide uppercase">Neo-Colab</div>
                    <div className="flex-1 flex flex-col items-center justify-center text-center mt-3 bg-[#1e293b]/20 border border-dashed border-slate-800 rounded-xl p-3">
                      <BookMarked className="w-6 h-6 text-slate-600 mb-1" />
                      <span className="text-xs text-slate-400 font-semibold">No Colab Courses Taken</span>
                      <span className="text-[10px] text-slate-500 mt-0.5">Enroll in active coding tracks</span>
                    </div>
                  </div>

                  <div className="glass-card p-5 flex flex-col justify-between h-44 hover:border-slate-600 transition-all select-none">
                    <div className="text-sm font-bold text-slate-300 tracking-wide uppercase">Solved Questions</div>
                    <div className="flex items-center gap-4 mt-3">
                      <div className="relative w-20 h-20 flex items-center justify-center shrink-0">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="40" cy="40" r="34" className="stroke-dark-border" strokeWidth="6" fill="transparent" />
                          <circle cx="40" cy="40" r="34" className="stroke-[#2563eb] transition-all duration-500 ease-out" strokeWidth="6" fill="transparent" strokeDasharray={2 * Math.PI * 34} strokeDashoffset={2 * Math.PI * 34 * (1 - percentage / 100)} strokeLinecap="round" />
                        </svg>
                        <div className="absolute flex flex-col items-center justify-center">
                          <span className="text-base font-bold text-dark-text">{solvedCount}</span>
                          <span className="text-[8px] text-dark-muted font-bold uppercase tracking-wider">Solved</span>
                        </div>
                      </div>
                      <div className="flex-1 space-y-1.5">
                        <div className="flex justify-between items-center text-xs font-semibold">
                          <span className="text-slate-400">Easy</span>
                          <span className="text-emerald-400">{lc?.easy ?? leetcode?.stats?.easy_solved ?? 0}</span>
                        </div>
                        <div className="flex justify-between items-center text-xs font-semibold">
                          <span className="text-slate-400">Medium</span>
                          <span className="text-amber-400">{lc?.medium ?? leetcode?.stats?.medium_solved ?? 0}</span>
                        </div>
                        <div className="flex justify-between items-center text-xs font-semibold">
                          <span className="text-slate-400">Hard</span>
                          <span className="text-rose-400">{lc?.hard ?? leetcode?.stats?.hard_solved ?? 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  {leetcode?.has_data && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-card p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="section-title flex items-center gap-2">
                          <Code2 className="w-5 h-5 text-primary" />
                          LeetCode Activity
                        </h2>
                        <span className="text-sm text-dark-muted font-medium">Last 365 days</span>
                      </div>
                      <LeetCodeHeatmap data={leetcode.heatmap} />
                      <div className="mt-5 grid grid-cols-3 gap-4 border-t border-dark-border/40 pt-4">
                        {Object.entries(leetcode.difficulty_distribution ?? {}).map(([diff, count]) => (
                          <div key={diff} className="text-center">
                            <p className="text-xl font-bold text-dark-text">{count as number}</p>
                            <p className="text-xs text-dark-muted font-medium mt-0.5">{diff} Solved</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {github?.has_data && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="section-title flex items-center gap-2">
                          <GitBranch className="w-5 h-5 text-success" />
                          GitHub Contributions
                        </h2>
                        <span className="text-sm text-dark-muted font-medium">{github.stats?.total_commits ?? 0} contributions</span>
                      </div>
                      <GitHubContributionGraph data={github.contribution_graph} />

                      {Object.keys(github.top_languages ?? {}).length > 0 && (
                        <div className="mt-5 border-t border-dark-border/40 pt-4">
                          <p className="text-xs font-bold text-dark-text uppercase tracking-wider mb-3">Top Languages</p>
                          <div className="flex gap-2 flex-wrap">
                            {Object.entries(github.top_languages ?? {}).slice(0, 6).map(([lang, count]) => (
                              <span key={lang} className="stat-badge bg-dark-card border border-dark-border text-dark-muted">
                                {lang} <span className="text-primary font-bold">{count as number}</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}

                  <div className="grid lg:grid-cols-2 gap-6">
                    <AIAnalysisCard userId={user?.id} />
                    <AchievementsPanel achievements={achievements?.achievements ?? []} />
                  </div>
                </div>
              </motion.div>
            )}

            {currentTab === "courses" && (
              <motion.div
                key="courses-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div>
                  <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
                    My Courses
                  </h1>
                  <p className="text-dark-muted text-sm mt-1">
                    Manage and track your Neo-Colab progress and active training courses
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[
                    { title: "Data Structures & Algorithms", code: "CS301", progress: 85, status: "Active", instructor: "Dr. K. Srinivasan", sessions: "24/28" },
                    { title: "Java Programming Essentials", code: "CS302", progress: 100, status: "Completed", instructor: "Mrs. M. Priya", sessions: "20/20" },
                    { title: "Python for AI & Data Science", code: "CS305", progress: 42, status: "Active", instructor: "Dr. A. Rajesh", sessions: "10/24" },
                    { title: "Advanced DBMS & SQL", code: "CS308", progress: 15, status: "Active", instructor: "Mrs. S. Latha", sessions: "3/20" }
                  ].map((course) => (
                    <div key={course.code} className="glass-card p-6 flex flex-col justify-between hover:border-slate-600 transition-all select-none">
                      <div>
                        <div className="flex justify-between items-start">
                          <span className="text-xs font-bold text-primary uppercase tracking-wider px-2 py-0.5 rounded bg-primary/10 border border-primary/20">
                            {course.code}
                          </span>
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                            course.status === "Completed" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}>
                            {course.status}
                          </span>
                        </div>
                        <h3 className="text-lg font-bold text-white mt-3 leading-snug">{course.title}</h3>
                        <p className="text-xs text-dark-muted mt-1">Instructor: {course.instructor}</p>
                      </div>

                      <div className="mt-6 space-y-2">
                        <div className="flex justify-between text-xs font-semibold text-slate-300">
                          <span>Progress</span>
                          <span>{course.progress}% ({course.sessions} sessions)</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-dark-border overflow-hidden">
                          <div className="h-full bg-primary rounded-full" style={{ width: `${course.progress}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {currentTab === "drives" && (
              <motion.div
                key="drives-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div>
                  <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
                    Placement Drives
                  </h1>
                  <p className="text-dark-muted text-sm mt-1">
                    Ongoing and upcoming placement campaigns and corporate eligibility check
                  </p>
                </div>

                <div className="glass-card overflow-hidden">
                  <div className="p-4 border-b border-dark-border/40 bg-dark-card/30 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Active Placement Drives</span>
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                      Eligible for 4 campaigns
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-dark-muted uppercase bg-dark-card/50">
                        <tr>
                          <th className="px-6 py-3">Company</th>
                          <th className="px-6 py-3">Role</th>
                          <th className="px-6 py-3">Drive Date</th>
                          <th className="px-6 py-3">Eligibility</th>
                          <th className="px-6 py-3">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          { company: "Zoho Corporation", role: "Software Developer", date: "15 Jul 2026", criteria: "CGPA >= 7.5", status: "Applied" },
                          { company: "TCS Digital", role: "System Engineer", date: "22 Jul 2026", criteria: "CGPA >= 6.5", status: "Eligible" },
                          { company: "Wipro Turbo", role: "Project Engineer", date: "05 Aug 2026", criteria: "CS/IT only", status: "Closed" },
                          { company: "Cognizant GenC", role: "Programmer Analyst", date: "12 Aug 2026", criteria: "CGPA >= 6.0", status: "Upcoming" }
                        ].map((drive, idx) => (
                          <tr key={idx} className="border-b border-dark-border/30 last:border-0 hover:bg-dark-card/20 transition-all">
                            <td className="px-6 py-4 font-bold text-white flex items-center gap-2">
                              <Building className="w-4 h-4 text-slate-400" />
                              {drive.company}
                            </td>
                            <td className="px-6 py-4 text-slate-300">{drive.role}</td>
                            <td className="px-6 py-4 text-slate-400 font-medium">{drive.date}</td>
                            <td className="px-6 py-4 text-xs text-dark-muted font-medium">{drive.criteria}</td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                                drive.status === "Applied" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" :
                                drive.status === "Eligible" ? "bg-primary/20 text-primary border border-primary/30" :
                                drive.status === "Closed" ? "bg-red-500/20 text-red-400 border border-red-500/30" :
                                "bg-slate-700/20 text-slate-300 border border-slate-700/30"
                              }`}>
                                {drive.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            )}

            {currentTab === "contest" && (
              <motion.div
                key="contest-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="glass-card p-6 text-center select-none max-w-lg mx-auto">
                  <Trophy className="w-12 h-12 text-[#2563eb] mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-white">Upcoming Coding Contest</h3>
                  <p className="text-sm text-dark-muted mt-2">
                    LeetCode Weekly Contest 410 is scheduled for Sunday.
                  </p>
                  <button className="bg-primary hover:bg-primary/90 text-white font-bold py-2 px-6 rounded-xl mt-6 cursor-pointer">Register</button>
                </div>
              </motion.div>
            )}

            {currentTab === "company-tests" && (
              <motion.div
                key="company-tests-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="glass-card p-6 text-center select-none max-w-lg mx-auto">
                  <Award className="w-12 h-12 text-primary mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-white">Accenture Prep Test Active</h3>
                  <p className="text-sm text-dark-muted mt-2">
                    A test session covering cognitive and coding assessment is available.
                  </p>
                  <button className="bg-primary hover:bg-primary/90 text-white font-bold py-2 px-6 rounded-xl mt-6 cursor-pointer">Start Mock Test</button>
                </div>
              </motion.div>
            )}

            {currentTab === "leaderboard" && (
              <motion.div
                key="leaderboard-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2 max-w-4xl mx-auto">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-amber-500" />
                      VSB Leaderboards
                    </h2>
                    <p className="text-xs text-dark-muted mt-0.5">Ranked standings across multiple performance categories</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5 p-1 bg-dark-card border border-dark-border/40 rounded-xl">
                    {[
                      { key: "overall", label: "Overall Score" },
                      { key: "solved", label: "Problem Solvers" },
                      { key: "commits", label: "Committers" },
                      { key: "streak", label: "Streak" },
                      { key: "contest", label: "Contest Rating" },
                      { key: "repos", label: "Repo Creators" },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setLeaderboardMetric(tab.key)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                          leaderboardMetric === tab.key
                            ? "bg-primary text-black font-bold"
                            : "text-dark-muted hover:text-dark-text"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="glass-card overflow-hidden max-w-4xl mx-auto">
                  <table className="w-full text-sm text-left border-collapse">
                    <thead>
                      <tr className="text-dark-muted text-xs uppercase bg-dark-card/50 border-b border-dark-border/30">
                        <th className="px-6 py-3.5 text-center font-bold w-16">Rank</th>
                        <th className="px-6 py-3.5 font-bold">Name</th>
                        <th className="px-6 py-3.5 text-center font-bold">Year</th>
                        <th className="px-6 py-3.5 text-center font-bold">Solved</th>
                        <th className="px-6 py-3.5 text-center font-bold">Commits</th>
                        <th className="px-6 py-3.5 text-center font-bold">Streak</th>
                        <th className="px-6 py-3.5 text-center font-bold">Contest Rating</th>
                        <th className="px-6 py-3.5 text-center font-bold">Overall Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-border/10">
                      {leaderboard?.items?.map((item: any) => {
                        const isMe = item.full_name === user?.full_name;
                        return (
                          <tr 
                            key={item.user_id} 
                            className={`transition-colors duration-150 ${
                              isMe ? "bg-primary/10 text-white font-semibold" : "text-dark-text hover:bg-dark-card/25"
                            }`}
                          >
                            <td className="px-6 py-4 text-center">
                              {item.rank === 1 ? (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-500 font-bold border border-amber-500/30">1</span>
                              ) : item.rank === 2 ? (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-300/20 text-slate-300 font-bold border border-slate-300/30">2</span>
                              ) : item.rank === 3 ? (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-700/20 text-orange-700 font-bold border border-orange-700/30">3</span>
                              ) : (
                                <span className="text-dark-muted">{item.rank}</span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <div className="font-semibold">{item.full_name}</div>
                              {isMe && <span className="text-[10px] text-primary uppercase font-bold bg-primary/20 px-1.5 py-0.5 rounded mt-0.5 inline-block">You</span>}
                            </td>
                            <td className="px-6 py-4 text-center">{item.year ? `${item.year}rd Year` : "3rd Year"}</td>
                            <td className="px-6 py-4 text-center font-mono">{item.problems_solved}</td>
                            <td className="px-6 py-4 text-center font-mono">{item.commits}</td>
                            <td className="px-6 py-4 text-center font-mono">{item.streak}d</td>
                            <td className="px-6 py-4 text-center font-mono">{item.contest_rating?.toFixed(1) || "0.0"}</td>
                            <td className="px-6 py-4 text-center font-bold text-amber-500">{item.total_score?.toFixed(1)}</td>
                          </tr>
                        );
                      })}
                      {(!leaderboard || leaderboard.items?.length === 0) && (
                        <tr>
                          <td colSpan={8} className="text-center py-12 text-dark-muted">
                            Loading leaderboards...
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {currentTab === "engagement" && (
              <motion.div
                key="engagement-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="glass-card p-6 text-center select-none max-w-lg mx-auto">
                  <MessageSquare className="w-12 h-12 text-[#22D3EE] mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-white">Mentor Review Scheduled</h3>
                  <p className="text-sm text-dark-muted mt-2">
                    Your mentor has scheduled a progress review meeting for next Friday.
                  </p>
                </div>
              </motion.div>
            )}

            {currentTab === "nerd" && (
              <motion.div
                key="nerd-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="p-6 lg:p-8 space-y-6"
              >
                <div className="glass-card p-8 text-center select-none max-w-lg mx-auto">
                  <Grid className="w-16 h-16 text-primary mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white">Access Academic Records on NERD</h3>
                  <a href="https://nerd.vsb.edu.in" target="_blank" rel="noopener noreferrer" className="btn-primary mt-6 inline-flex items-center gap-2 cursor-pointer">
                    Launch NERD Portal <ArrowRight className="w-4 h-4" />
                  </a>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function StudentDashboard() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-dark-bg text-dark-text">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-medium">Loading Dashboard...</p>
        </div>
      </div>
    }>
      <StudentDashboardContent />
    </Suspense>
  );
}
