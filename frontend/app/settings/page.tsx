"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Settings,
  Shield,
  Bell,
  Save,
  Key,
  Users,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "@/components/layout/Sidebar";
import api from "@/lib/api";
import toast from "react-hot-toast";

interface AdminAccount {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export default function SettingsPage() {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);

  // Admin account management state
  const [adminAccounts, setAdminAccounts] = useState<AdminAccount[]>([]);
  const [loadingAdmins, setLoadingAdmins] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState<string>("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [updatingPassword, setUpdatingPassword] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  // Fetch admin accounts on mount
  useEffect(() => {
    if (isAuthenticated && user?.role?.name === "admin") {
      fetchAdminAccounts();
    }
  }, [isAuthenticated, user]);

  const fetchAdminAccounts = async () => {
    setLoadingAdmins(true);
    try {
      const { data } = await api.get("/admin/admin-accounts");
      setAdminAccounts(data.admins || []);
      if (data.admins?.length > 0 && !selectedAdmin) {
        setSelectedAdmin(data.admins[0].email);
      }
    } catch {
      toast.error("Failed to load admin accounts");
    } finally {
      setLoadingAdmins(false);
    }
  };

  const validatePassword = (pwd: string): string[] => {
    const errors: string[] = [];
    if (pwd.length < 8) errors.push("At least 8 characters");
    if (!/[A-Z]/.test(pwd)) errors.push("One uppercase letter");
    if (!/[a-z]/.test(pwd)) errors.push("One lowercase letter");
    if (!/\d/.test(pwd)) errors.push("One digit");
    return errors;
  };

  const handlePasswordChange = (pwd: string) => {
    setNewPassword(pwd);
    setPasswordErrors(validatePassword(pwd));
  };

  const handleUpdateCredentials = async () => {
    if (!selectedAdmin) {
      toast.error("Select an admin account");
      return;
    }
    if (!newPassword) {
      toast.error("Enter a new password");
      return;
    }
    const errors = validatePassword(newPassword);
    if (errors.length > 0) {
      toast.error("Password does not meet requirements");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setUpdatingPassword(true);
    try {
      const { data } = await api.patch("/admin/update-admin-credentials", {
        admin_email: selectedAdmin,
        new_password: newPassword,
      });
      toast.success(data.message || "Password updated successfully!");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordErrors([]);
    } catch (err: any) {
      toast.error(
        err?.response?.data?.detail || "Failed to update credentials"
      );
    } finally {
      setUpdatingPassword(false);
    }
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      toast.success("Settings saved successfully!");
      setIsSaving(false);
    }, 1000);
  };

  const isAdmin = user?.role?.name === "admin";

  return (
    <div className="flex h-screen overflow-hidden bg-dark-bg">
      <Sidebar role={(user?.role?.name as "admin" | "staff" | "student") || "admin"} />

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 lg:p-8 space-y-8 max-w-4xl mx-auto">
          <div>
            <h1 className="text-2xl lg:text-3xl font-display font-bold text-dark-text">
              System Settings
            </h1>
            <p className="text-dark-muted mt-1">Configure global platform preferences</p>
          </div>

          <div className="space-y-6">
            {/* ─── Admin Account Management ──────────────────────────── */}
            {isAdmin && (
              <div className="glass-card p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-amber-500/20 text-amber-500 rounded-lg">
                    <Key className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-dark-text">
                      Admin Account Management
                    </h2>
                    <p className="text-sm text-dark-muted">
                      Manage admin credentials and access
                    </p>
                  </div>
                </div>

                {/* Admin Accounts List */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-medium text-dark-text flex items-center gap-2">
                      <Users className="w-4 h-4 text-dark-muted" />
                      Admin Accounts
                    </label>
                    <button
                      onClick={fetchAdminAccounts}
                      disabled={loadingAdmins}
                      className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 transition-colors"
                    >
                      <RefreshCw className={`w-3 h-3 ${loadingAdmins ? "animate-spin" : ""}`} />
                      Refresh
                    </button>
                  </div>

                  {loadingAdmins ? (
                    <div className="flex items-center gap-2 text-dark-muted text-sm py-3">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading admin accounts...
                    </div>
                  ) : adminAccounts.length === 0 ? (
                    <p className="text-sm text-dark-muted py-3">No admin accounts found.</p>
                  ) : (
                    <div className="space-y-2">
                      {adminAccounts.map((admin) => (
                        <button
                          key={admin.id}
                          onClick={() => setSelectedAdmin(admin.email)}
                          className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all text-left ${
                            selectedAdmin === admin.email
                              ? "border-primary bg-primary/10"
                              : "border-dark-border bg-dark-surface hover:border-dark-border/80"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                                selectedAdmin === admin.email
                                  ? "bg-primary/20 text-primary"
                                  : "bg-dark-border text-dark-muted"
                              }`}
                            >
                              {admin.full_name.charAt(0)}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-dark-text">
                                {admin.full_name}
                              </p>
                              <p className="text-xs text-dark-muted font-mono">
                                {admin.email}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                                admin.is_active
                                  ? "bg-green-500/20 text-green-400"
                                  : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {admin.is_active ? "Active" : "Inactive"}
                            </span>
                            {admin.last_login_at && (
                              <p className="text-[10px] text-dark-muted mt-1">
                                Last login:{" "}
                                {new Date(admin.last_login_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <hr className="border-dark-border/50 mb-6" />

                {/* Change Password Section */}
                <div>
                  <h3 className="text-sm font-semibold text-dark-text mb-4 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-primary" />
                    Change Admin Password
                  </h3>

                  <div className="space-y-4">
                    {/* Selected Admin */}
                    <div>
                      <label className="block text-xs font-medium text-dark-muted mb-1.5">
                        Selected Admin
                      </label>
                      <select
                        value={selectedAdmin}
                        onChange={(e) => setSelectedAdmin(e.target.value)}
                        className="w-full bg-dark-surface border border-dark-border text-dark-text text-sm rounded-lg focus:ring-primary focus:border-primary p-2.5"
                      >
                        {adminAccounts.map((a) => (
                          <option key={a.id} value={a.email}>
                            {a.full_name} ({a.email})
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* New Password */}
                    <div>
                      <label className="block text-xs font-medium text-dark-muted mb-1.5">
                        New Password
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? "text" : "password"}
                          value={newPassword}
                          onChange={(e) => handlePasswordChange(e.target.value)}
                          placeholder="Enter new password"
                          className="w-full bg-dark-surface border border-dark-border text-dark-text text-sm rounded-lg focus:ring-primary focus:border-primary p-2.5 pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-muted hover:text-dark-text transition-colors"
                        >
                          {showPassword ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      {/* Password Requirements */}
                      {newPassword.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {[
                            { label: "At least 8 characters", ok: newPassword.length >= 8 },
                            { label: "One uppercase letter", ok: /[A-Z]/.test(newPassword) },
                            { label: "One lowercase letter", ok: /[a-z]/.test(newPassword) },
                            { label: "One digit", ok: /\d/.test(newPassword) },
                          ].map(({ label, ok }) => (
                            <div
                              key={label}
                              className={`flex items-center gap-1.5 text-xs ${
                                ok ? "text-green-400" : "text-dark-muted"
                              }`}
                            >
                              {ok ? (
                                <CheckCircle2 className="w-3 h-3" />
                              ) : (
                                <AlertTriangle className="w-3 h-3" />
                              )}
                              {label}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Confirm Password */}
                    <div>
                      <label className="block text-xs font-medium text-dark-muted mb-1.5">
                        Confirm Password
                      </label>
                      <input
                        type={showPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm new password"
                        className={`w-full bg-dark-surface border text-dark-text text-sm rounded-lg focus:ring-primary focus:border-primary p-2.5 ${
                          confirmPassword && confirmPassword !== newPassword
                            ? "border-red-500"
                            : "border-dark-border"
                        }`}
                      />
                      {confirmPassword && confirmPassword !== newPassword && (
                        <p className="mt-1 text-xs text-red-400">Passwords do not match</p>
                      )}
                    </div>

                    {/* Submit Button */}
                    <button
                      onClick={handleUpdateCredentials}
                      disabled={
                        updatingPassword ||
                        !newPassword ||
                        !confirmPassword ||
                        newPassword !== confirmPassword ||
                        passwordErrors.length > 0
                      }
                      className="w-full sm:w-auto flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      {updatingPassword ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Updating...
                        </>
                      ) : (
                        <>
                          <Key className="w-4 h-4" />
                          Update Password
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ─── Security & Authentication ──────────────────────────── */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-primary/20 text-primary rounded-lg">
                  <Shield className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold text-dark-text">Security & Authentication</h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-text">Two-Factor Authentication (2FA)</p>
                    <p className="text-sm text-dark-muted">Require 2FA for all Admin and Staff accounts</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-dark-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
                <hr className="border-dark-border/50" />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-text">Session Timeout</p>
                    <p className="text-sm text-dark-muted">Automatically log users out after inactivity</p>
                  </div>
                  <select className="bg-dark-surface border border-dark-border text-dark-text text-sm rounded-lg focus:ring-primary focus:border-primary block p-2.5">
                    <option>15 Minutes</option>
                    <option>30 Minutes</option>
                    <option>1 Hour</option>
                    <option>24 Hours</option>
                  </select>
                </div>
              </div>
            </div>

            {/* ─── Notifications ──────────────────────────────────────── */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-secondary/20 text-secondary rounded-lg">
                  <Bell className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold text-dark-text">Notifications</h2>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-dark-text">System Alerts</p>
                    <p className="text-sm text-dark-muted">Email alerts for platform downtime or sync failures</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-dark-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-secondary"></div>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="btn-primary flex items-center gap-2"
              >
                {isSaving ? (
                  <span className="animate-pulse">Saving...</span>
                ) : (
                  <>
                    <Save className="w-4 h-4" /> Save Configuration
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
