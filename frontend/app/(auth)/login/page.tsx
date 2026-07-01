"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2, Code2, GitBranch, Trophy, Zap, GraduationCap, Users } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import toast from "react-hot-toast";

const FEATURES = [
  { icon: Code2, label: "LeetCode Tracking", desc: "Real-time problem stats & heatmaps" },
  { icon: GitBranch, label: "GitHub Analytics", desc: "Commits, PRs, contribution graphs" },
  { icon: Trophy, label: "Leaderboards", desc: "Department & global rankings" },
  { icon: Zap, label: "AI Analysis", desc: "Gemini-powered insights & recommendations" },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"student" | "staff">("student");
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate() {
    const errs: Record<string, string> = {};
    if (!form.email) {
      errs.email = "Email or Username is required";
    }
    if (!form.password) {
      errs.password = "Password is required";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const emailLower = form.email.toLowerCase().trim();
    if (emailLower.includes("admin")) {
      toast.error("Administrative access is restricted on this portal. Please use the secure admin route.");
      return;
    }

    try {
      await login(form.email, form.password, false);
      toast.success("Welcome back! 🎉");
      
      const user = useAuthStore.getState().user;
      const role = user?.role?.name;
      if (role === "admin") {
        router.push("/dashboard/admin");
      } else if (role === "staff") {
        router.push("/dashboard/staff");
      } else {
        router.push("/dashboard/student");
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Invalid email/username or password");
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* ── Left: Branding Panel ── */}
      <div className="relative hidden lg:flex flex-col justify-between p-12 overflow-hidden border-r border-dark-border"
           style={{ background: "linear-gradient(145deg, #FFFDF0 0%, #FFFBE6 50%, #FEF9C3 100%)" }}>
        {/* Animated background orbs */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full opacity-20"
               style={{ background: "radial-gradient(circle, #EAB308, transparent)" }} />
          <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full opacity-15"
               style={{ background: "radial-gradient(circle, #F59E0B, transparent)" }} />
        </div>

        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center p-1.5 shadow-sm">
            <img src="/vsb-logo.png" alt="VSB Logo" className="w-8 h-8 object-contain" />
          </div>
          <div>
            <p className="text-lg font-display font-bold text-slate-900">CodePulse AI</p>
            <p className="text-xs text-slate-600">VSB Engineering College</p>
          </div>
        </motion.div>

        {/* Main headline */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="relative z-10"
        >
          <h1 className="text-4xl font-display font-bold text-slate-900 mb-4 leading-tight">
            Track. Analyze.<br />
            <span className="gradient-text">Excel.</span>
          </h1>
          <p className="text-slate-600 text-lg mb-8">
            AI-powered coding analytics for placement readiness. Monitor 10,000+ students in real-time.
          </p>

          {/* Feature grid */}
          <div className="grid grid-cols-2 gap-4">
            {FEATURES.map(({ icon: Icon, label, desc }) => (
              <motion.div
                key={label}
                whileHover={{ scale: 1.02 }}
                className="glass-card p-4"
              >
                <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center mb-2">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <p className="text-sm font-semibold text-dark-text">{label}</p>
                <p className="text-xs text-dark-muted mt-0.5">{desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <p className="relative z-10 text-xs text-slate-600">
          Developed by Abish & Anand · © 2025 CodePulse AI · VSB Engineering College. All rights reserved.
        </p>
      </div>

      {/* ── Right: Login Form ── */}
      <div className="flex items-center justify-center p-6 lg:p-12 bg-dark-bg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center p-1 shadow-sm">
              <img src="/vsb-logo.png" alt="VSB Logo" className="w-7 h-7 object-contain" />
            </div>
            <p className="text-lg font-display font-bold text-white">CodePulse AI</p>
          </div>

          <h2 className="text-3xl font-display font-bold text-dark-text mb-1">VSB Portal Login</h2>
          <p className="text-dark-muted mb-6">Sign in to access your dashboard</p>

          {/* ERP Tab Selectors */}
          <div className="grid grid-cols-2 p-1 bg-dark-card border border-dark-border rounded-xl mb-6">
            <button
              onClick={() => {
                setActiveTab("student");
                setForm({ email: "", password: "" });
                setErrors({});
              }}
              className={`flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all ${
                activeTab === "student"
                  ? "bg-primary text-slate-900 font-bold shadow-sm"
                  : "text-dark-muted hover:text-dark-text"
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              Student Login
            </button>
            <button
              onClick={() => {
                setActiveTab("staff");
                setForm({ email: "", password: "" });
                setErrors({});
              }}
              className={`flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all ${
                activeTab === "staff"
                  ? "bg-primary text-slate-900 font-bold shadow-sm"
                  : "text-dark-muted hover:text-dark-text"
              }`}
            >
              <Users className="w-4 h-4" />
              Staff Login
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email / Username */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-dark-text mb-1.5">
                {activeTab === "student" ? "Student Email or Username" : "Faculty Email or Username"}
              </label>
              <input
                id="email"
                type="text"
                placeholder={activeTab === "student" ? "student1@vsb.edu.in or student1" : "staff1@vsb.edu.in or staff1"}
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={`input-field ${errors.email ? "border-danger focus:ring-danger/50" : ""}`}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-danger">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="text-sm font-medium text-dark-text">
                  Password
                </label>
                <Link href="/forgot-password" className="text-xs text-primary hover:text-primary-light transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className={`input-field pr-10 ${errors.password ? "border-danger focus:ring-danger/50" : ""}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-muted hover:text-dark-text transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-danger">{errors.password}</p>
              )}
            </div>

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileTap={{ scale: 0.98 }}
              className="btn-primary w-full py-3 text-base disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                `Sign in as ${activeTab === "student" ? "Student" : "Faculty"}`
              )}
            </motion.button>
          </form>

          <p className="mt-6 text-center text-sm text-dark-muted">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary hover:text-primary-light font-medium transition-colors">
              Create account
            </Link>
          </p>

          {/* Demo credentials */}
          <div className="mt-6 p-4 rounded-xl border border-dark-border bg-dark-card/50">
            <p className="text-xs text-dark-muted font-medium mb-2">Demo Credentials</p>
            <div className="space-y-1 font-mono text-xs">
              <p className="text-dark-muted">Student: <span className="text-primary">student1</span> / <span className="text-primary">Student@123</span></p>
              <p className="text-dark-muted">Staff: <span className="text-secondary">staff1</span> / <span className="text-secondary">Staff@123</span></p>
            </div>
          </div>
          
          <div className="mt-8 text-center text-[10px] text-dark-muted font-semibold font-mono">
            Developed by Abish & Anand ❤️
          </div>
        </motion.div>
      </div>
    </div>
  );
}
