"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, Download, FileSpreadsheet, Loader2, Sparkles, X } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import toast from "react-hot-toast";

export default function ReportsPage() {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [isExportingExcel, setIsExportingExcel] = useState(false);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [aiReport, setAiReport] = useState<any>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      const response = await api.get("/reports/excel", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `codepulse_report_${new Date().toISOString().split("T")[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel report downloaded successfully!");
    } catch (error) {
      toast.error("Failed to generate Excel report");
    } finally {
      setIsExportingExcel(false);
    }
  };

  const handleGenerateAIReport = async () => {
    setIsGeneratingAI(true);
    try {
      const response = await api.post("/ai/global-report");
      setAiReport(response.data);
      toast.success("Global AI Report generated!");
    } catch (error) {
      toast.error("Failed to generate AI report");
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const role = user?.role?.name as "student" | "staff" | "admin" || "staff";

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role={role} />

      <main className="flex-1 overflow-y-auto relative">
        <div className="p-6 lg:p-8 space-y-8">
          <div>
            <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">Reports & Exports</h1>
            <p className="text-dark-muted mt-1">Generate and download performance reports.</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="glass-card p-6 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mb-4">
                <FileSpreadsheet className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-xl font-bold text-dark-text mb-2">Master Excel Report</h2>
              <p className="text-sm text-dark-muted mb-6">
                Complete data dump of all students, scores, and classifications for offline analysis.
              </p>
              <button
                onClick={handleExportExcel}
                disabled={isExportingExcel || role === "student"}
                className="btn-primary w-full max-w-xs mt-auto"
              >
                {isExportingExcel ? <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> : <Download className="w-4 h-4 mr-2 inline" />}
                Download Excel
              </button>
              {role === "student" && <p className="text-xs text-danger mt-2">Admin/Staff access required</p>}
            </div>

            <div className="glass-card p-6 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-warning/20 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-warning" />
              </div>
              <h2 className="text-xl font-bold text-dark-text mb-2">Global AI Analysis</h2>
              <p className="text-sm text-dark-muted mb-6">
                Generate an AI-powered institution-wide performance report focusing on LeetCode & GitHub.
              </p>
              <button
                onClick={handleGenerateAIReport}
                disabled={isGeneratingAI || role === "student"}
                className="btn-primary w-full max-w-xs mt-auto bg-warning hover:bg-warning/90 text-dark-bg"
              >
                {isGeneratingAI ? <Loader2 className="w-4 h-4 animate-spin mr-2 inline" /> : <Sparkles className="w-4 h-4 mr-2 inline" />}
                Generate AI Report
              </button>
              {role === "student" && <p className="text-xs text-danger mt-2">Admin access required</p>}
            </div>
            
            <div className="glass-card p-6 flex flex-col items-center text-center opacity-60">
              <div className="w-16 h-16 bg-secondary/20 rounded-full flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-secondary" />
              </div>
              <h2 className="text-xl font-bold text-dark-text mb-2">Individual PDFs</h2>
              <p className="text-sm text-dark-muted mb-6">
                Go to a student&apos;s profile to download their individual detailed PDF report.
              </p>
              <button disabled className="btn-primary w-full max-w-xs mt-auto opacity-50 cursor-not-allowed">
                Go to Profiles
              </button>
            </div>
          </div>
        </div>

        {/* AI Report Modal */}
        {aiReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-dark-card w-full max-w-2xl rounded-xl shadow-2xl border border-warning/30 overflow-hidden max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between p-6 border-b border-dark-border bg-warning/10">
                <h2 className="text-2xl font-bold text-warning flex items-center gap-2">
                  <Sparkles className="w-6 h-6" /> Institution Analytics Report
                </h2>
                <button onClick={() => setAiReport(null)} className="text-gray-400 hover:text-white">
                  <X size={24} />
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-dark-text mb-2 border-b border-dark-border pb-1">Platform Summary</h3>
                  <p className="text-dark-muted leading-relaxed">{aiReport.platform_summary}</p>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-warning mb-2 border-b border-dark-border pb-1">LeetCode Analysis</h3>
                    <p className="text-dark-muted leading-relaxed text-sm">{aiReport.leetcode_analysis}</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-success mb-2 border-b border-dark-border pb-1">GitHub Analysis</h3>
                    <p className="text-dark-muted leading-relaxed text-sm">{aiReport.github_analysis}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-primary mb-2 border-b border-dark-border pb-1">Strategic Recommendations</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {aiReport.strategic_recommendations?.map((rec: string, i: number) => (
                      <li key={i} className="text-dark-muted text-sm">{rec}</li>
                    ))}
                  </ul>
                </div>

                {aiReport.top_students?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-secondary mb-2 border-b border-dark-border pb-1">Top Performing Students</h3>
                    <div className="flex flex-wrap gap-2">
                      {aiReport.top_students.map((student: string, i: number) => (
                        <span key={i} className="px-3 py-1 bg-secondary/20 text-secondary rounded-full text-xs font-medium">
                          {student}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-center text-gray-500 pt-4 border-t border-dark-border">
                  Generated at: {new Date(aiReport.generated_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
