"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Users, Mail, BookOpen, UserPlus, Trash2, RefreshCw, Loader2, Shield, Database } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { AddUserModal } from "@/components/admin/AddUserModal";
import toast from "react-hot-toast";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function StudentDirectory() {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [isSyncingAll, setIsSyncingAll] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; name: string } | null>(null);
  const [isReseeding, setIsReseeding] = useState(false);

  const handleReseed = async () => {
    setIsReseeding(true);
    const toastId = toast.loading("Re-seeding database... This may take a moment.");
    try {
      await api.post("/admin/reseed");
      toast.success("Database re-seeded successfully! Refreshing...", { id: toastId });
      mutate();
    } catch {
      toast.error("Failed to re-seed database", { id: toastId });
    } finally {
      setIsReseeding(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data, error, isLoading, mutate } = useSWR("/admin/users?role=student&page_size=100", fetcher);

  const handleSync = async (userId: string, name: string) => {
    setSyncingId(userId);
    try {
      const res = await api.post(`/admin/users/${userId}/sync`);
      toast.success(`Synced ${name}! LC: ${res.data.leetcode?.total_solved ?? 0} solved`);
      mutate();
    } catch {
      toast.error(`Failed to sync ${name}`);
    } finally {
      setSyncingId(null);
    }
  };

  const handleSyncAll = async () => {
    setIsSyncingAll(true);
    const toastId = toast.loading("Syncing all students... This may take a moment.");
    try {
      const res = await api.post("/admin/sync-all");
      toast.success(`Successfully synced ${res.data.synced} members!`, { id: toastId });
      mutate();
    } catch {
      toast.error("Failed to sync all members", { id: toastId });
    } finally {
      setIsSyncingAll(false);
    }
  };

  const handleDelete = async (userId: string, hard = false) => {
    setDeletingId(userId);
    try {
      await api.delete(`/admin/users/${userId}?hard=${hard}`);
      toast.success(hard ? "Student permanently deleted." : "Student deactivated.");
      setConfirmDelete(null);
      mutate();
    } catch {
      toast.error("Failed to delete student");
    } finally {
      setDeletingId(null);
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const toastId = toast.loading("Uploading and importing CSV user roster...");
    try {
      const res = await api.post("/admin/bulk-import-csv", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      const { imported, errors } = res.data;
      if (errors && errors.length > 0) {
        toast.error(`Imported ${imported} users. Errors: ${errors.join(", ")}`, { id: toastId, duration: 6000 });
      } else {
        toast.success(`Successfully imported ${imported} users from CSV!`, { id: toastId });
      }
      mutate();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to upload CSV roster", { id: toastId });
    }
  };

  const role = (user?.role?.name as "admin" | "staff" | "student") || "admin";

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role={role} />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
                Student Directory
              </h1>
              <p className="text-dark-muted mt-1">Manage and view all enrolled students</p>
            </div>
            <div className="flex items-center gap-3">
              {role === "admin" && (
                <label
                  className="flex items-center gap-2 bg-dark-surface hover:bg-dark-surface/80 border border-dark-border text-dark-text px-4 py-2 rounded-lg cursor-pointer transition-colors font-medium text-sm"
                >
                  <Database size={18} />
                  <span>Upload CSV</span>
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={handleCSVUpload}
                  />
                </label>
              )}
              <button
                onClick={handleSyncAll}
                disabled={isSyncingAll}
                className="flex items-center gap-2 bg-dark-surface hover:bg-dark-surface/80 border border-dark-border text-dark-text px-4 py-2 rounded-lg transition-colors disabled:opacity-50 font-medium text-sm"
              >
                {isSyncingAll ? (
                  <Loader2 size={18} className="animate-spin text-primary" />
                ) : (
                  <RefreshCw size={18} />
                )}
                <span>Sync All</span>
              </button>
              {role === "admin" && (
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg transition-colors shadow-lg shadow-primary/20 text-sm font-semibold"
                >
                  <UserPlus size={18} />
                  <span>Add Student</span>
                </button>
              )}
            </div>
          </div>

          <AddUserModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            role="student"
            onSuccess={() => mutate()}
          />

          <div className="glass-card p-6">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <p className="text-dark-muted animate-pulse">Loading student directory...</p>
                <p className="text-xs text-dark-muted/60">This may take a moment if the server is waking up.</p>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                  <Database className="w-6 h-6 text-red-400" />
                </div>
                <div className="text-center">
                  <p className="text-red-400 font-medium">Failed to load student data.</p>
                  <p className="text-sm text-dark-muted mt-1">The server may be starting up or the data needs to be re-seeded.</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => mutate()}
                    className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg transition-colors text-sm font-semibold shadow-lg shadow-primary/20"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Retry
                  </button>
                  {role === "admin" && (
                    <button
                      onClick={handleReseed}
                      disabled={isReseeding}
                      className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-slate-900 px-4 py-2 rounded-lg transition-colors text-sm font-semibold disabled:opacity-50"
                    >
                      {isReseeding ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Database className="w-4 h-4" />
                      )}
                      {isReseeding ? "Re-seeding..." : "Re-seed Database"}
                    </button>
                  )}
                </div>
              </div>
            ) : data?.items?.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <Users className="w-12 h-12 text-dark-muted/40" />
                <div className="text-center">
                  <p className="text-dark-muted font-medium">No students found.</p>
                  <p className="text-sm text-dark-muted/60 mt-1">Add students manually or re-seed the database.</p>
                </div>
                {role === "admin" && (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setIsModalOpen(true)}
                      className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg transition-colors text-sm font-semibold"
                    >
                      <UserPlus className="w-4 h-4" />
                      Add Student
                    </button>
                    <button
                      onClick={handleReseed}
                      disabled={isReseeding}
                      className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-slate-900 px-4 py-2 rounded-lg transition-colors text-sm font-semibold disabled:opacity-50"
                    >
                      {isReseeding ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Database className="w-4 h-4" />
                      )}
                      {isReseeding ? "Re-seeding..." : "Re-seed Database"}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-dark-border">
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Student Name</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Email</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Department</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">LeetCode Solved</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">GitHub Commits</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Status</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.items?.map((student: any) => (
                      <tr key={student.id} className="border-b border-dark-border/50 hover:bg-dark-surface/50 transition-colors">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-secondary/20 text-secondary flex items-center justify-center font-bold">
                              {student.full_name.charAt(0)}
                            </div>
                            <div>
                              <span className="font-medium text-dark-text block">{student.full_name}</span>
                              <span className="text-xs text-dark-muted block font-mono">
                                {student.reg_no || "N/A"} · Yr {student.year || "?"}{student.section ? `-${student.section}` : ""}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm text-dark-muted">
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" /> {student.email}
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm text-dark-muted">
                          <div className="flex items-center gap-2">
                            <BookOpen className="w-4 h-4" /> {student.department?.code || "N/A"}
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm font-mono font-semibold text-warning">
                          <span className="block">{student.leetcode_stats?.total_solved ?? 0}</span>
                          <span className="text-xs text-dark-muted font-normal block font-sans">
                            ID: {student.leetcode_username || "N/A"}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-sm font-mono font-semibold text-success">
                          <span className="block">{student.github_stats?.total_commits ?? 0}</span>
                          <span className="text-xs text-dark-muted font-normal block font-sans">
                            ID: {student.github_username || "N/A"}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${student.is_active ? 'bg-success/20 text-success' : 'bg-red-500/20 text-red-500'}`}>
                            {student.is_active ? "Enrolled" : "Inactive"}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleSync(student.id, student.full_name)}
                              disabled={syncingId === student.id}
                              title="Sync LeetCode & GitHub data now"
                              className="p-1.5 rounded-lg text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
                            >
                              {syncingId === student.id
                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                : <RefreshCw className="w-4 h-4" />
                              }
                            </button>
                            <button
                              onClick={() => setConfirmDelete({ id: student.id, name: student.full_name })}
                              title="Delete student"
                              className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-dark-card w-full max-w-sm rounded-xl shadow-2xl border border-red-500/30 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="font-bold text-dark-text">Delete Student</h3>
                <p className="text-sm text-dark-muted">{confirmDelete.name}</p>
              </div>
            </div>
            <p className="text-sm text-dark-muted mb-6">
              Choose how you want to remove this student account:
            </p>
            <div className="flex flex-col gap-3">
              <button
                onClick={() => handleDelete(confirmDelete.id, false)}
                disabled={!!deletingId}
                className="w-full px-4 py-2 rounded-lg bg-warning/20 text-warning hover:bg-warning/30 transition-colors text-sm font-semibold flex items-center justify-center gap-2"
              >
                {deletingId ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
                Deactivate Only (keeps data)
              </button>
              <button
                onClick={() => handleDelete(confirmDelete.id, true)}
                disabled={!!deletingId}
                className="w-full px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-sm font-semibold flex items-center justify-center gap-2"
              >
                {deletingId ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                Permanently Delete
              </button>
              <button
                onClick={() => setConfirmDelete(null)}
                className="w-full px-4 py-2 rounded-lg border border-dark-border text-dark-muted hover:text-dark-text transition-colors text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
