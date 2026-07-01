import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { toast } from "react-hot-toast";

interface AddUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  role: "student" | "staff";
  onSuccess: () => void;
}

export function AddUserModal({ isOpen, onClose, role, onSuccess }: AddUserModalProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    department_code: "",
    reg_no: "",
    year: "",
    section: "",
    employee_id: "",
    designation: "",
    leetcode_username: "",
    github_username: "",
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload: any = {
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        role: role,
        department_code: formData.department_code || null,
        leetcode_username: formData.leetcode_username || null,
        github_username: formData.github_username || null,
      };

      if (role === "student") {
        payload.reg_no = formData.reg_no || null;
        payload.year = formData.year ? parseInt(formData.year) : null;
        payload.section = formData.section || null;
      } else if (role === "staff") {
        payload.employee_id = formData.employee_id || null;
        payload.designation = formData.designation || null;
      }

      await api.post("/admin/users", payload);
      toast.success(`${role === "student" ? "Student" : "Staff"} added successfully!`);
      onSuccess();
      onClose();
      // Reset form
      setFormData({
        email: "", password: "", full_name: "", department_code: "",
        reg_no: "", year: "", section: "", employee_id: "", designation: "",
        leetcode_username: "", github_username: ""
      });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to add user");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-dark-card w-full max-w-md rounded-xl shadow-2xl border border-dark-border overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <h2 className="text-xl font-bold text-dark-text capitalize">Add New {role}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Full Name *</label>
            <input
              required
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
              placeholder="John Doe"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Email Address *</label>
            <input
              required
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
              placeholder="john@vsb.edu.in"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Temporary Password * (min 8 chars)</label>
            <input
              required
              type="password"
              name="password"
              minLength={8}
              value={formData.password}
              onChange={handleChange}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
              placeholder="••••••••"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Department Code (Optional)</label>
            <input
              type="text"
              name="department_code"
              value={formData.department_code}
              onChange={handleChange}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
              placeholder="e.g. CSE"
            />
          </div>

          {role === "student" && (
            <>
              <div className="space-y-1">
                <label className="text-sm text-gray-400">Registration Number</label>
                <input
                  type="text"
                  name="reg_no"
                  value={formData.reg_no}
                  onChange={handleChange}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                  placeholder="e.g. 732921104001"
                />
              </div>
              <div className="flex gap-4">
                <div className="space-y-1 flex-1">
                  <label className="text-sm text-gray-400">Year</label>
                  <select
                    name="year"
                    value={formData.year}
                    onChange={handleChange}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                  >
                    <option value="">Select Year</option>
                    <option value="1">1st Year</option>
                    <option value="2">2nd Year</option>
                    <option value="3">3rd Year</option>
                    <option value="4">4th Year</option>
                  </select>
                </div>
                <div className="space-y-1 flex-1">
                  <label className="text-sm text-gray-400">Section</label>
                  <input
                    type="text"
                    name="section"
                    value={formData.section}
                    onChange={handleChange}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                    placeholder="e.g. A"
                  />
                </div>
              </div>
            </>
          )}

          {role === "staff" && (
            <>
              <div className="space-y-1">
                <label className="text-sm text-gray-400">Employee ID</label>
                <input
                  type="text"
                  name="employee_id"
                  value={formData.employee_id}
                  onChange={handleChange}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                  placeholder="e.g. EMP001"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm text-gray-400">Designation</label>
                <input
                  type="text"
                  name="designation"
                  value={formData.designation}
                  onChange={handleChange}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                  placeholder="e.g. Assistant Professor"
                />
              </div>
            </>
          )}

          <div className="flex gap-4 border-t border-dark-border pt-4">
            <div className="space-y-1 flex-1">
              <label className="text-sm text-gray-400">LeetCode ID</label>
              <input
                type="text"
                name="leetcode_username"
                value={formData.leetcode_username}
                onChange={handleChange}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                placeholder="e.g. abish05"
              />
            </div>
            <div className="space-y-1 flex-1">
              <label className="text-sm text-gray-400">GitHub ID</label>
              <input
                type="text"
                name="github_username"
                value={formData.github_username}
                onChange={handleChange}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-dark-text focus:outline-none focus:border-primary"
                placeholder="e.g. abish05"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-dark-border transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg flex items-center justify-center min-w-[100px] transition-colors"
            >
              {loading ? <Loader2 size={20} className="animate-spin" /> : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
