"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Mail, Building, UserPlus, Trash2, RefreshCw, Loader2, Shield, Database } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import { AddUserModal } from "@/components/admin/AddUserModal";
import toast from "react-hot-toast";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function StaffDirectory() {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [isSyncingAll, setIsSyncingAll] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; name: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data, error, isLoading, mutate } = useSWR("/admin/users?role=staff&page_size=100", fetcher);

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
    const toastId = toast.loading("Syncing all members... This may take a moment.");
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
      toast.success(hard ? "Staff member permanently deleted." : "Staff member deactivated.");
      setConfirmDelete(null);
      mutate();
    } catch {
      toast.error("Failed to delete staff member");
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
                Staff Directory
              </h1>
              <p className="text-dark-muted mt-1">Manage and view all faculty members</p>
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
                  <span>Add Staff</span>
                </button>
              )}
            </div>
          </div>

          <AddUserModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            role="staff"
            onSuccess={() => mutate()}
          />

          <div className="glass-card p-6">
            {isLoading ? (
              <div className="text-dark-muted animate-pulse">Loading staff directory...</div>
            ) : error ? (
              <div className="text-red-400">Failed to load staff data.</div>
            ) : data?.items?.length === 0 ? (
              <div className="text-dark-muted">No staff members found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-dark-border">
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Name</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Email</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Department</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">LeetCode Solved</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">GitHub Commits</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Status</th>
                      <th className="py-3 px-4 text-sm font-semibold text-dark-muted">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.items?.map((staff: any) => (
                      <tr key={staff.id} className="border-b border-dark-border/50 hover:bg-dark-surface/50 transition-colors">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                              {staff.full_name.charAt(0)}
                            </div>
                            <div>
                              <span className="font-medium text-dark-text block">{staff.full_name}</span>
                              <span className="text-xs text-dark-muted block font-mono">
                                {staff.employee_id || "N/A"} {staff.designation ? `· ${staff.designation}` : ""}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm text-dark-muted">
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" /> {staff.email}
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm text-dark-muted">
                          <div className="flex items-center gap-2">
                            <Building className="w-4 h-4" /> {staff.department?.code || "N/A"}
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm font-mono font-semibold text-warning">
                          <span className="block">{staff.leetcode_stats?.total_solved ?? 0}</span>
                          <span className="text-xs text-dark-muted font-normal block font-sans">
                            ID: {staff.leetcode_username || "N/A"}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-sm font-mono font-semibold text-success">
                          <span className="block">{staff.github_stats?.total_commits ?? 0}</span>
                          <span className="text-xs text-dark-muted font-normal block font-sans">
                            ID: {staff.github_username || "N/A"}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${staff.is_active ? 'bg-success/20 text-success' : 'bg-red-500/20 text-red-500'}`}>
                            {staff.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleSync(staff.id, staff.full_name)}
                              disabled={syncingId === staff.id}
                              title="Sync LeetCode & GitHub data now"
                              className="p-1.5 rounded-lg text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
                            >
                              {syncingId === staff.id
                                ? <Loader2 className="w-4 h-4 animate-spin" />
                                : <RefreshCw className="w-4 h-4" />
                              }
                            </button>
                            <button
                              onClick={() => setConfirmDelete({ id: staff.id, name: staff.full_name })}
                              title="Delete staff"
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
                <h3 className="font-bold text-dark-text">Remove Staff Member</h3>
                <p className="text-sm text-dark-muted">{confirmDelete.name}</p>
              </div>
            </div>
            <p className="text-sm text-dark-muted mb-6">
              Choose how you want to remove this staff account:
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
