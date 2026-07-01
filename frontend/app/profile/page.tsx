"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { User as UserIcon, Save, Loader2, Link as LinkIcon, Code2, GitBranch } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import toast from "react-hot-toast";
import useSWR from "swr";

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function ProfilePage() {
  const { user, isAuthenticated, fetchMe } = useAuthStore();
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({ leetcode_username: "", github_username: "" });

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const { data: profileData } = useSWR(user ? `/users/me/profile` : null, fetcher);

  useEffect(() => {
    if (profileData) {
      setForm({
        leetcode_username: profileData.leetcode_username || "",
        github_username: profileData.github_username || "",
      });
    }
  }, [profileData]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await api.put(`/users/me/profile`, form);
      await fetchMe();
      toast.success("Profile updated! The system will sync your data shortly.");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  const role = user?.role?.name as "student" | "staff" | "admin" || "student";

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role={role} />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
          <div>
            <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">My Profile</h1>
            <p className="text-dark-muted mt-1">Manage your account and connected platforms.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-1 glass-card p-6 flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-primary/20 rounded-full flex items-center justify-center text-primary text-3xl font-bold mb-4">
                {user?.full_name?.[0]?.toUpperCase()}
              </div>
              <h2 className="text-lg font-bold text-dark-text">{user?.full_name}</h2>
              <p className="text-sm text-dark-muted capitalize mb-1">{role}</p>
              <p className="text-xs text-dark-muted">{user?.email}</p>
            </div>

            <div className="md:col-span-2 glass-card p-6">
              <h2 className="section-title mb-6 flex items-center gap-2">
                <LinkIcon className="w-5 h-5 text-primary" /> Connected Platforms
              </h2>
              
              <form onSubmit={handleSave} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2 flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-warning" /> LeetCode Username
                  </label>
                  <input
                    type="text"
                    value={form.leetcode_username}
                    onChange={(e) => setForm({ ...form, leetcode_username: e.target.value })}
                    placeholder="e.g. john_doe"
                    className="input-field"
                  />
                  <p className="text-xs text-dark-muted mt-1">Required to track problems solved and contest ratings.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-text mb-2 flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-success" /> GitHub Username
                  </label>
                  <input
                    type="text"
                    value={form.github_username}
                    onChange={(e) => setForm({ ...form, github_username: e.target.value })}
                    placeholder="e.g. johndoe"
                    className="input-field"
                  />
                  <p className="text-xs text-dark-muted mt-1">Required to track commits and repositories.</p>
                </div>

                <div className="pt-4 border-t border-dark-border">
                  <button type="submit" disabled={isSaving} className="btn-primary">
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
