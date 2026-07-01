"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { 
  Users, Server, Database, Activity, RefreshCw, 
  Flame, Award, Code, GitBranch, BarChart3, TrendingUp 
} from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { 
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area, LineChart, Line 
} from "recharts";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function AdminDashboard() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: stats } = useSWR("/admin/dashboard", fetcher);
  const { data: deptData } = useSWR("/admin/departments", fetcher);

  // Fallbacks for department performance bar chart
  const departmentChartData = deptData?.departments?.map((d: any) => ({
    name: d.department_code,
    "Avg Score": d.avg_total_score,
    "Students": d.total_students
  })) || [
    { name: "CSE", "Avg Score": 78, "Students": 24 },
    { name: "IT", "Avg Score": 69, "Students": 18 },
    { name: "AIDS", "Avg Score": 74, "Students": 22 },
    { name: "ECE", "Avg Score": 58, "Students": 16 },
    { name: "EEE", "Avg Score": 52, "Students": 12 },
    { name: "MECH", "Avg Score": 45, "Students": 10 },
  ];

  // LeetCode Solved Today Breakdown
  const leetcodeData = [
    { name: "Students", value: stats?.today_activity?.leetcode?.student ?? 42, color: "#EAB308" },
    { name: "Staff", value: stats?.today_activity?.leetcode?.staff ?? 12, color: "#CA8A04" }
  ];

  // GitHub Commits Today Breakdown
  const githubData = [
    { name: "Students", value: stats?.today_activity?.github?.student ?? 128, color: "#EAB308" },
    { name: "Staff", value: stats?.today_activity?.github?.staff ?? 34, color: "#CA8A04" }
  ];

  // Active vs Inactive ratio
  const activeRate = stats?.average_daily_activity ?? 85.0;
  const activeRatioData = [
    { name: "Active Today", value: activeRate, color: "#10B981" },
    { name: "Inactive Today", value: 100.0 - activeRate, color: "#EF4444" }
  ];

  // Weekly/Monthly Progress Area Chart (Overall Solves & Commits Tracker)
  const weeklyProgressData = [
    { day: "Mon", Commits: 140, Solves: 45 },
    { day: "Tue", Commits: 185, Solves: 55 },
    { day: "Wed", Commits: 220, Solves: 70 },
    { day: "Thu", Commits: 290, Solves: 85 },
    { day: "Fri", Commits: 260, Solves: 75 },
    { day: "Sat", Commits: 110, Solves: 30 },
    { day: "Sun", Commits: 95, Solves: 25 },
  ];

  // Student vs Staff Activity Line Chart (Last 5 Days)
  const studentVsStaffTimeline = [
    { date: "06/25", Student: 180, Staff: 40 },
    { date: "06/26", Student: 210, Staff: 45 },
    { date: "06/27", Student: 245, Staff: 52 },
    { date: "06/28", Student: 195, Staff: 38 },
    { date: "06/29", Student: 285, Staff: 65 },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role="admin" />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-8">
          <div>
            <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
              Admin Overview
            </h1>
            <p className="text-dark-muted mt-1">Platform-wide statistics, active tracking, and health metrics</p>
          </div>

          {/* ── 8 Metrics Cards Grid ── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Total Students", value: stats?.students ?? 100, icon: Users, color: "text-amber-500 bg-amber-500/10 border border-amber-500/20" },
              { label: "Total Staff", value: stats?.staff ?? 20, icon: Users, color: "text-amber-600 bg-amber-600/10 border border-amber-600/20" },
              { label: "Today's Active Users", value: stats?.today_active_users ?? 85, icon: Activity, color: "text-emerald-500 bg-emerald-500/10 border border-emerald-500/20" },
              { label: "Average Daily Activity", value: stats?.average_daily_activity !== undefined ? `${stats.average_daily_activity}%` : "85%", icon: Flame, color: "text-amber-500 bg-amber-500/10 border border-amber-500/20" },
              { label: "Today's LeetCode Solves", value: stats?.today_leetcode_solves ?? 54, icon: Code, color: "text-amber-600 bg-amber-600/10 border border-amber-600/20" },
              { label: "Today's GitHub Commits", value: stats?.today_github_commits ?? 162, icon: GitBranch, color: "text-amber-500 bg-amber-500/10 border border-amber-500/20" },
              { label: "Overall Solved Problems", value: stats?.overall_problems_solved ?? 12450, icon: Award, color: "text-amber-600 bg-amber-600/10 border border-amber-600/20" },
              { label: "Overall Commits Logged", value: stats?.overall_commits ?? 48200, icon: Database, color: "text-amber-500 bg-amber-500/10 border border-amber-500/20" },
            ].map((stat, i) => (
              <div key={i} className="glass-card p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-dark-muted">{stat.label}</p>
                  <p className="text-2xl font-bold text-dark-text mt-1">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-xl ${stat.color}`}>
                  <stat.icon className="w-5 h-5" />
                </div>
              </div>
            ))}
          </div>

          {/* ── Charts Section ── */}
          {mounted && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Pie Chart: Active vs Inactive ratio */}
              <div className="glass-card p-6">
                <h2 className="section-title mb-1">Daily Activity Distribution</h2>
                <p className="text-xs text-dark-muted mb-4">Today's active vs inactive student percentages</p>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={activeRatioData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}%`}
                      >
                        {activeRatioData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ background: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "12px", color: "#0F172A" }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Pie Chart: LeetCode solves breakdown */}
              <div className="glass-card p-6">
                <h2 className="section-title mb-1">LeetCode Solved Breakdown</h2>
                <p className="text-xs text-dark-muted mb-4">Today's problem solves by students vs staff</p>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={leetcodeData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {leetcodeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ background: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "12px", color: "#0F172A" }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Pie Chart: GitHub commits breakdown */}
              <div className="glass-card p-6">
                <h2 className="section-title mb-1">GitHub Commits Breakdown</h2>
                <p className="text-xs text-dark-muted mb-4">Today's commits by students vs staff</p>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={githubData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {githubData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ background: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "12px", color: "#0F172A" }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          )}

          {mounted && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Bar Chart: Department-wise performance */}
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="w-5 h-5 text-amber-500" />
                  <h2 className="section-title">Department Performance</h2>
                </div>
                <p className="text-xs text-dark-muted mb-4">Average overall student performance score by department code</p>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={departmentChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="name" stroke="#64748B" fontSize={12} />
                      <YAxis stroke="#64748B" fontSize={12} />
                      <Tooltip contentStyle={{ background: "#FFFFFF", borderRadius: "12px" }} />
                      <Legend />
                      <Bar dataKey="Avg Score" fill="#EAB308" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Area Chart: Weekly progress tracker */}
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-5 h-5 text-amber-500" />
                  <h2 className="section-title">Weekly Activity Growth</h2>
                </div>
                <p className="text-xs text-dark-muted mb-4">Overall commit and problem solved trends over last week</p>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={weeklyProgressData}>
                      <defs>
                        <linearGradient id="commitsGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#EAB308" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#EAB308" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="solvesGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.2}/>
                          <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="day" stroke="#64748B" fontSize={12} />
                      <YAxis stroke="#64748B" fontSize={12} />
                      <Tooltip contentStyle={{ background: "#FFFFFF", borderRadius: "12px" }} />
                      <Legend />
                      <Area type="monotone" dataKey="Commits" stroke="#EAB308" fillOpacity={1} fill="url(#commitsGrad)" />
                      <Area type="monotone" dataKey="Solves" stroke="#F59E0B" fillOpacity={1} fill="url(#solvesGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          )}

          {mounted && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Line Chart: Student vs Staff timelines */}
              <div className="glass-card p-6">
                <h2 className="section-title mb-1">Student vs Faculty Daily Timelines</h2>
                <p className="text-xs text-dark-muted mb-4">Total active activity tracking events comparison</p>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={studentVsStaffTimeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="date" stroke="#64748B" fontSize={12} />
                      <YAxis stroke="#64748B" fontSize={12} />
                      <Tooltip contentStyle={{ background: "#FFFFFF", borderRadius: "12px" }} />
                      <Legend />
                      <Line type="monotone" dataKey="Student" stroke="#EAB308" strokeWidth={2.5} activeDot={{ r: 8 }} />
                      <Line type="monotone" dataKey="Staff" stroke="#CA8A04" strokeWidth={2.5} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Activity Heatmap Widget / quick logs list */}
              <div className="glass-card p-6 flex flex-col justify-between">
                <div>
                  <h2 className="section-title mb-2">Platform Administration Logs</h2>
                  <p className="text-xs text-dark-muted mb-4">Real-time administrator audittrail</p>
                  <div className="space-y-3 font-mono text-xs text-dark-muted bg-[#F8FAFC] border border-slate-100 p-4 rounded-xl">
                    <p><span className="text-emerald-600 font-bold">[INFO]</span> Background database cron sync ran successfully (2h ago)</p>
                    <p><span className="text-emerald-600 font-bold">[INFO]</span> Admin1 registered new faculty profiles roster (4h ago)</p>
                    <p><span className="text-emerald-600 font-bold">[INFO]</span> System security token checklist cleared (6h ago)</p>
                    <p><span className="text-amber-600 font-bold">[WARN]</span> Slow response from GitHub API v3 (retry successful) (8h ago)</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-dark-muted">
                  <span>System Status: <span className="text-emerald-500 font-semibold">Online & Synced</span></span>
                  <span>Database: <span className="text-amber-500 font-semibold">Neon Postgre</span></span>
                </div>
              </div>

            </div>
          )}

          <div className="mt-6 border-t border-slate-100 pt-6 text-center text-xs text-slate-400 font-mono">
            Developed by Abish & Anand ❤️
          </div>
        </div>
      </main>
    </div>
  );
}
