/**
 * Zustand auth store with persist middleware
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import api, { registerAuthCallbacks } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: { name: string };
  department?: { code: string; name: string } | null;
  is_active: boolean;
  avatar_url?: string | null;
  reg_no?: string | null;
  year?: number | null;
  section?: string | null;
  leetcode_username?: string | null;
  github_username?: string | null;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string, is_admin_portal?: boolean) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
  clearAuth: () => void;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role: "student" | "staff" | "admin";
  department_code?: string;
  reg_no?: string;
  year?: number;
  section?: string;
  employee_id?: string;
  designation?: string;
  leetcode_username?: string;
  github_username?: string;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      isAuthenticated: false,
 
      setTokens: (access, refresh) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
      },
 
      clearAuth: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },
 
      login: async (email, password, is_admin_portal = false) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post("/auth/login", { email, password, is_admin_portal });
          get().setTokens(data.access_token, data.refresh_token);
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (registerData) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post("/auth/register", registerData);
          get().setTokens(data.access_token, data.refresh_token);
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        const { refreshToken, clearAuth } = get();
        try {
          if (refreshToken) {
            await api.post("/auth/logout", { refresh_token: refreshToken });
          }
        } catch {
          // Ignore logout errors
        } finally {
          clearAuth();
        }
      },

      fetchMe: async () => {
        try {
          const { data } = await api.get("/users/me");
          set({ user: data, isAuthenticated: true });
        } catch {
          get().clearAuth();
        }
      },
    }),
    {
      name: "codepulse-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

if (typeof window !== "undefined") {
  registerAuthCallbacks(
    (access, refresh) => {
      useAuthStore.setState({
        accessToken: access,
        refreshToken: refresh,
        isAuthenticated: true,
      });
    },
    () => {
      useAuthStore.getState().clearAuth();
    }
  );
}
