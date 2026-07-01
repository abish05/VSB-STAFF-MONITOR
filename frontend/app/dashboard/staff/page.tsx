"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import useSWR from "swr";
import { motion } from "framer-motion";
import { Users, AlertCircle, TrendingUp, Search, Filter, Loader2, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { ScoreGauge } from "@/components/charts/ScoreGauge";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function StaffDashboard() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: stats } = useSWR("/staff/dashboard", fetcher);
  const { data: students, isLoading: studentsLoading } = useSWR(
    `/staff/mentees?search=${searchTerm}`,
    fetcher
  );

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role="staff" />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
                Staff Dashboard
              </h1>
              <p className="text-dark-muted mt-1">
                Monitor your department&apos;s performance
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass-card p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/20 rounded-lg"><Users className="w-5 h-5 text-primary" /></div>
                <p className="text-sm font-semibold text-dark-text">Total Students</p>
              </div>
              <p className="text-3xl font-bold text-dark-text">{stats?.total_students ?? 0}</p>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-warning/20 rounded-lg"><AlertCircle className="w-5 h-5 text-warning" /></div>
                <p className="text-sm font-semibold text-dark-text">Needs Attention</p>
              </div>
              <p className="text-3xl font-bold text-dark-text">{stats?.needs_attention ?? 0}</p>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-success/20 rounded-lg"><TrendingUp className="w-5 h-5 text-success" /></div>
                <p className="text-sm font-semibold text-dark-text">Avg Placement Score</p>
              </div>
              <p className="text-3xl font-bold text-dark-text">{stats?.avg_placement_score?.toFixed(1) ?? 0}</p>
            </div>
          </div>

          {/* Student Search & List */}
          <div className="glass-card p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
              <h2 className="section-title">Student Directory</h2>
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-dark-muted" />
                <input
                  type="text"
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input-field pl-9 h-10 py-0"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Reg No</th>
                    <th>LC Score</th>
                    <th>GH Score</th>
                    <th>Total Score</th>
                    <th>Classification</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {studentsLoading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-primary mx-auto" />
                      </td>
                    </tr>
                  ) : students?.items?.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-dark-muted">
                        No students found.
                      </td>
                    </tr>
                  ) : (
                    students?.items?.map((student: any) => (
                      <tr key={student.id}>
                        <td>
                          <p className="font-semibold text-dark-text">{student.full_name}</p>
                          <p className="text-xs text-dark-muted">{student.email}</p>
                        </td>
                        <td className="font-mono text-xs text-dark-muted">{student.profile?.reg_no || "-"}</td>
                        <td>{student.performance?.leetcode_score?.toFixed(0) || 0}</td>
                        <td>{student.performance?.github_score?.toFixed(0) || 0}</td>
                        <td className="font-bold text-primary">{student.performance?.total_score?.toFixed(1) || 0}</td>
                        <td>
                          <span className={
                            student.performance?.classification === "Excellent" ? "badge-excellent" :
                            student.performance?.classification === "Good" ? "badge-good" :
                            student.performance?.classification === "Average" ? "badge-average" : "badge-needs-improvement"
                          }>
                            {student.performance?.classification || "Unknown"}
                          </span>
                        </td>
                        <td>
                          <Link href={`/dashboard/student/${student.id}`} className="btn-ghost px-3 py-1">
                            View <ArrowRight className="w-4 h-4 ml-1" />
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
