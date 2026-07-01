"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Users, FileText, Settings, User as UserIcon,
  LogOut, GraduationCap, BookOpen, Trophy, Briefcase, Award, BarChart3, MessageSquare, Grid
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  tab?: string;
}

export function Sidebar({ role, activeTab }: { role: "student" | "staff" | "admin"; activeTab?: string }) {
  const pathname = usePathname();
  const currentTab = activeTab || "skill";
  const { logout, user } = useAuthStore();

  const navItems: Record<"student" | "staff" | "admin", NavItem[]> = {
    student: [
      { href: "/dashboard/student", tab: "skill", label: "Dashboard", icon: LayoutDashboard },
      { href: "/dashboard/student?tab=courses", tab: "courses", label: "Courses", icon: BookOpen },
      { href: "/dashboard/student?tab=contest", tab: "contest", label: "Contest", icon: Trophy },
      { href: "/dashboard/student?tab=drives", tab: "drives", label: "Drives", icon: Briefcase },
      { href: "/dashboard/student?tab=company-tests", tab: "company-tests", label: "Company Specific Test", icon: Award },
      { href: "/dashboard/student?tab=leaderboard", tab: "leaderboard", label: "Leaderboard", icon: BarChart3 },
      { href: "/dashboard/student?tab=engagement", tab: "engagement", label: "Engagement", icon: MessageSquare },
      { href: "/dashboard/student?tab=nerd", tab: "nerd", label: "Go to NERD", icon: Grid },
    ],
    staff: [
      { href: "/dashboard/staff", label: "Dashboard", icon: LayoutDashboard },
      { href: "/students", label: "Students", icon: Users },
      { href: "/reports", label: "Reports", icon: FileText },
      { href: "/profile", label: "Profile", icon: UserIcon },
    ],
    admin: [
      { href: "/dashboard/admin", label: "Overview", icon: LayoutDashboard },
      { href: "/staff", label: "Staff", icon: GraduationCap },
      { href: "/students", label: "Students", icon: Users },
      { href: "/reports", label: "Reports", icon: FileText },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  };

  const links = navItems[role] || [];

  if (role === "student") {
    // Narrow vertical layout matching screenshot
    return (
      <aside className="w-24 bg-dark-card border-r border-dark-border flex flex-col h-full shrink-0 text-dark-text select-none">
        {/* Logo */}
        <div className="p-4 flex justify-center border-b border-dark-border">
          <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center p-1 shadow-md hover:scale-105 transition-transform duration-200">
            <img src="/vsb-logo.png" alt="VSB Logo" className="w-10 h-10 object-contain" />
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto space-y-3 px-1 no-scrollbar">
          {links.map((link) => {
            const isActive = link.tab ? currentTab === link.tab : pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.label}
                href={link.href}
                className={`flex flex-col items-center justify-center py-2 px-1 rounded-xl text-center transition-all duration-200 relative group cursor-pointer ${
                  isActive
                    ? "bg-primary text-black font-semibold shadow-md"
                    : "text-dark-muted hover:text-dark-text hover:bg-dark-bg"
                }`}
              >
                <Icon className={`w-5 h-5 mb-1 ${isActive ? "text-black" : "text-dark-muted group-hover:text-dark-text"}`} />
                <span className="text-[10px] leading-tight break-words w-full px-0.5 tracking-wide">
                  {link.label}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-dot"
                    className="absolute left-0 w-1 h-8 bg-black rounded-r-full"
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer actions */}
        <div className="p-3 border-t border-dark-border flex flex-col items-center gap-3">
          <Link
            href="/profile"
            className="w-10 h-10 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-sm font-bold text-yellow-800 hover:bg-primary/30 transition-all cursor-pointer"
            title="Profile"
          >
            {user?.full_name?.[0]?.toUpperCase() || "A"}
          </Link>
          <button
            onClick={logout}
            className="p-2 rounded-xl text-red-500 hover:text-red-600 hover:bg-red-500/10 transition-all cursor-pointer"
            title="Sign Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </aside>
    );
  }

  // Regular sidebar for staff and admin
  return (
    <aside className="w-64 bg-dark-card border-r border-dark-border flex flex-col h-full shrink-0">
      <div className="p-6">
        <Link href={`/dashboard/${role}`} className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center p-1 shadow-sm">
            <img src="/vsb-logo.png" alt="VSB Logo" className="w-8 h-8 object-contain" />
          </div>
          <div>
            <span className="font-display font-bold text-base text-dark-text block leading-tight">VSB College</span>
            <span className="text-[10px] text-dark-muted font-medium uppercase tracking-wider block">
              {role} portal
            </span>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {links.map((link) => {
          const isActive = pathname.startsWith(link.href);
          const Icon = link.icon;
          return (
            <Link key={link.href} href={link.href} className={`nav-item ${isActive ? "active" : ""}`}>
              <Icon className="w-4 h-4" />
              {link.label}
              {isActive && (
                <motion.div layoutId="sidebar-active"
                  className="absolute left-0 w-1 h-8 bg-primary rounded-r-full" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-dark-border">
        <div className="flex items-center gap-3 mb-4 px-2">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-yellow-800 font-bold">
            {user?.full_name?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-dark-text truncate">{user?.full_name}</p>
            <p className="text-xs text-dark-muted truncate capitalize">{user?.role?.name}</p>
          </div>
        </div>
        <button onClick={logout} className="btn-ghost w-full justify-start text-danger hover:text-danger hover:bg-danger/10">
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
