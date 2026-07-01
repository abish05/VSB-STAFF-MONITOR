"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, Loader2, Zap, ChevronRight, ChevronLeft } from "lucide-react";
import { useAuthStore, RegisterData } from "@/stores/auth";
import toast from "react-hot-toast";

type Role = "student" | "staff";
type Step = 1 | 2 | 3;

const DEPARTMENTS = [
  { code: "CSE", label: "Computer Science & Engineering" },
  { code: "IT", label: "Information Technology" },
  { code: "AIDS", label: "AI & Data Science" },
  { code: "ECE", label: "Electronics & Communication" },
  { code: "EEE", label: "Electrical & Electronics" },
  { code: "MECH", label: "Mechanical Engineering" },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuthStore();
  const [step, setStep] = useState<Step>(1);
  const [role, setRole] = useState<Role>("student");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    department_code: "CSE",
    // Student
    reg_no: "",
    year: 1,
    section: "",
    // Staff
    employee_id: "",
    designation: "",
    // Platform IDs
    leetcode_username: "",
    github_username: "",
  });

  function update(field: string, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  }

  function validateStep1() {
    const errs: Record<string, string> = {};
    if (!form.full_name.trim()) errs.full_name = "Full name is required";
    if (!form.email) errs.email = "Email is required";
    else if (!/^[^@]+@[^@]+\.[^@]+$/.test(form.email)) errs.email = "Invalid email";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function validateStep2() {
    const errs: Record<string, string> = {};
    if (role === "student") {
      if (!form.reg_no.trim()) errs.reg_no = "Registration number is required";
    } else {
      if (!form.employee_id.trim()) errs.employee_id = "Employee ID is required";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function validateStep3() {
    const errs: Record<string, string> = {};
    if (form.password.length < 8) errs.password = "Minimum 8 characters";
    else if (!/[A-Z]/.test(form.password)) errs.password = "Must contain uppercase letter";
    else if (!/[0-9]/.test(form.password)) errs.password = "Must contain a number";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function next() {
    if (step === 1 && validateStep1()) setStep(2);
    else if (step === 2 && validateStep2()) setStep(3);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validateStep3()) return;

    const data: RegisterData = {
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      role,
      department_code: form.department_code,
      leetcode_username: form.leetcode_username || undefined,
      github_username: form.github_username || undefined,
      ...(role === "student"
        ? { reg_no: form.reg_no, year: form.year, section: form.section || undefined }
        : { employee_id: form.employee_id, designation: form.designation || undefined }),
    };

    try {
      await register(data);
      toast.success("Account created! Welcome to CodePulse 🎉");
      if (role === "student") router.push("/dashboard/student");
      else router.push("/dashboard/staff");
    } catch {
      // errors handled by interceptor
    }
  }

  const stepLabels = ["Personal Info", "Academic Details", "Set Password"];

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-dark-bg">
      {/* Background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 rounded-full opacity-10"
             style={{ background: "radial-gradient(circle, #6366F1, transparent)" }} />
        <div className="absolute bottom-1/4 -right-48 w-96 h-96 rounded-full opacity-10"
             style={{ background: "radial-gradient(circle, #22D3EE, transparent)" }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg relative"
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center p-1 shadow-sm">
            <img src="/vsb-logo.png" alt="VSB Logo" className="w-7 h-7 object-contain" />
          </div>
          <div>
            <p className="font-display font-bold text-dark-text font-bold">CodePulse AI</p>
            <p className="text-xs text-dark-muted">Create your account</p>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 mb-8">
          {stepLabels.map((label, idx) => (
            <div key={label} className="flex-1 flex items-center gap-2">
              <div className={`flex-1 flex flex-col items-center gap-1`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all
                  ${step > idx + 1 ? "bg-success text-white" : step === idx + 1 ? "text-black" : "bg-dark-card text-dark-muted border border-dark-border"}`}
                     style={step === idx + 1 ? { background: "linear-gradient(135deg, #EAB308, #F59E0B)" } : {}}>
                  {step > idx + 1 ? "✓" : idx + 1}
                </div>
                <p className={`text-xs hidden sm:block ${step === idx + 1 ? "text-primary" : "text-dark-muted"}`}>{label}</p>
              </div>
              {idx < 2 && <div className={`h-px flex-1 mb-5 ${step > idx + 1 ? "bg-success" : "bg-dark-border"}`} />}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="glass-card p-6 space-y-5">
            <AnimatePresence mode="wait">
              {step === 1 && (
                <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                  <h2 className="text-xl font-display font-bold text-dark-text">Personal Information</h2>

                  {/* Role Toggle */}
                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-2">I am a</label>
                    <div className="grid grid-cols-2 gap-3">
                      {(["student", "staff"] as Role[]).map((r) => (
                        <button key={r} type="button"
                          onClick={() => setRole(r)}
                          className={`py-2.5 rounded-xl text-sm font-semibold border transition-all capitalize
                            ${role === r ? "border-primary bg-primary/20 text-primary" : "border-dark-border text-dark-muted hover:border-primary/50"}`}>
                          {r}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-1.5">Full Name</label>
                    <input id="full-name" type="text" placeholder="Enter your full name" value={form.full_name}
                      onChange={(e) => update("full_name", e.target.value)}
                      className={`input-field ${errors.full_name ? "border-danger" : ""}`} />
                    {errors.full_name && <p className="mt-1 text-xs text-danger">{errors.full_name}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-1.5">Email</label>
                    <input id="email" type="email" placeholder="you@vsb.edu.in" value={form.email}
                      onChange={(e) => update("email", e.target.value)}
                      className={`input-field ${errors.email ? "border-danger" : ""}`} />
                    {errors.email && <p className="mt-1 text-xs text-danger">{errors.email}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-1.5">Department</label>
                    <select id="department" value={form.department_code}
                      onChange={(e) => update("department_code", e.target.value)}
                      className="input-field">
                      {DEPARTMENTS.map((d) => (
                        <option key={d.code} value={d.code}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                </motion.div>
              )}

              {step === 2 && (
                <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                  <h2 className="text-xl font-display font-bold text-dark-text">
                    {role === "student" ? "Academic Details" : "Staff Details"}
                  </h2>

                  {role === "student" ? (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-dark-text mb-1.5">Registration Number</label>
                        <input id="reg-no" type="text" placeholder="e.g. 23CSE001" value={form.reg_no}
                          onChange={(e) => update("reg_no", e.target.value.toUpperCase())}
                          className={`input-field font-mono ${errors.reg_no ? "border-danger" : ""}`} />
                        {errors.reg_no && <p className="mt-1 text-xs text-danger">{errors.reg_no}</p>}
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-dark-text mb-1.5">Year</label>
                          <select id="year" value={form.year} onChange={(e) => update("year", parseInt(e.target.value))} className="input-field">
                            {[1, 2, 3, 4].map((y) => <option key={y} value={y}>{y}{["st","nd","rd","th"][y-1]} Year</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-dark-text mb-1.5">Section (optional)</label>
                          <input id="section" type="text" placeholder="e.g. A" value={form.section}
                            onChange={(e) => update("section", e.target.value.toUpperCase())}
                            className="input-field" maxLength={5} />
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-dark-text mb-1.5">Employee ID</label>
                        <input id="employee-id" type="text" placeholder="e.g. VSB-STAFF-001" value={form.employee_id}
                          onChange={(e) => update("employee_id", e.target.value.toUpperCase())}
                          className={`input-field font-mono ${errors.employee_id ? "border-danger" : ""}`} />
                        {errors.employee_id && <p className="mt-1 text-xs text-danger">{errors.employee_id}</p>}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-dark-text mb-1.5">Designation (optional)</label>
                        <input id="designation" type="text" placeholder="e.g. Assistant Professor" value={form.designation}
                          onChange={(e) => update("designation", e.target.value)}
                          className="input-field" />
                      </div>
                    </>
                  )}

                  {/* Common Platform IDs for both Staff and Students */}
                  <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-dark-border">
                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-1.5">LeetCode ID</label>
                      <input id="leetcode-id" type="text" placeholder="e.g. abish05" value={form.leetcode_username}
                        onChange={(e) => update("leetcode_username", e.target.value)}
                        className="input-field" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-1.5">GitHub ID</label>
                      <input id="github-id" type="text" placeholder="e.g. abish05" value={form.github_username}
                        onChange={(e) => update("github_username", e.target.value)}
                        className="input-field" />
                    </div>
                  </div>
                </motion.div>
              )}

              {step === 3 && (
                <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                  <h2 className="text-xl font-display font-bold text-dark-text">Set Your Password</h2>
                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-1.5">Password</label>
                    <div className="relative">
                      <input id="password" type={showPassword ? "text" : "password"} placeholder="Min. 8 chars, 1 uppercase, 1 number"
                        value={form.password} onChange={(e) => update("password", e.target.value)}
                        className={`input-field pr-10 ${errors.password ? "border-danger" : ""}`} />
                      <button type="button" onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-muted hover:text-dark-text"
                        aria-label="Toggle password visibility">
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {errors.password && <p className="mt-1 text-xs text-danger">{errors.password}</p>}

                    {/* Password strength */}
                    {form.password && (
                      <div className="mt-2 space-y-1">
                        {[
                          { label: "8+ characters", ok: form.password.length >= 8 },
                          { label: "Uppercase letter", ok: /[A-Z]/.test(form.password) },
                          { label: "Number", ok: /[0-9]/.test(form.password) },
                          { label: "Special character", ok: /[!@#$%^&*]/.test(form.password) },
                        ].map(({ label, ok }) => (
                          <div key={label} className="flex items-center gap-2 text-xs">
                            <div className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-success" : "bg-dark-border"}`} />
                            <span className={ok ? "text-success" : "text-dark-muted"}>{label}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Navigation */}
            <div className="flex gap-3 pt-2">
              {step > 1 && (
                <button type="button" onClick={() => setStep((s) => (s - 1) as Step)} className="btn-secondary flex-1">
                  <ChevronLeft className="w-4 h-4" />
                  Back
                </button>
              )}
              {step < 3 ? (
                <button type="button" onClick={next} className="btn-primary flex-1">
                  Continue
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <motion.button type="submit" disabled={isLoading} whileTap={{ scale: 0.98 }}
                  className="btn-primary flex-1 disabled:opacity-60">
                  {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" />Creating account...</> : "Create Account"}
                </motion.button>
              )}
            </div>
          </div>
        </form>

        <p className="mt-6 text-center text-sm text-dark-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:text-primary-light font-medium">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}
