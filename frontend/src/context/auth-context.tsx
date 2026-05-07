"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiLogin, apiSignup, apiGetProfile, type UserProfile, type CareerResult } from "@/lib/api";

interface AuthState {
  isAuthenticated: boolean;
  username: string;
  profile: UserProfile;
  careerResult: CareerResult | null;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setCareerResult: (result: CareerResult) => void;
  setProfile: (profile: Partial<UserProfile> | ((prev: UserProfile) => UserProfile)) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    username: "",
    profile: {},
    careerResult: null,
  });

  // Restore session from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("career_mapper_session");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setState(parsed);
      } catch {
        localStorage.removeItem("career_mapper_session");
      }
    }
  }, []);

  // Persist session on change
  useEffect(() => {
    if (state.isAuthenticated) {
      localStorage.setItem("career_mapper_session", JSON.stringify(state));
    }
  }, [state]);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    setState({
      isAuthenticated: true,
      username: data.username,
      profile: data.profile,
      careerResult: data.profile.career_result || null,
    });
  }, []);

  const signup = useCallback(async (username: string, email: string, password: string) => {
    await apiSignup(username, email, password);
  }, []);

  const logout = useCallback(() => {
    setState({
      isAuthenticated: false,
      username: "",
      profile: {},
      careerResult: null,
    });
    localStorage.removeItem("career_mapper_session");
  }, []);

  const setCareerResult = useCallback((result: CareerResult) => {
    setState((s) => ({ ...s, careerResult: result }));
  }, []);

  const setProfile = useCallback((update: Partial<UserProfile> | ((prev: UserProfile) => UserProfile)) => {
    setState((s) => ({
      ...s,
      profile: typeof update === "function" ? update(s.profile) : { ...s.profile, ...update },
    }));
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!state.username) return;
    const profile = await apiGetProfile(state.username);
    setState((s) => ({
      ...s,
      profile,
      careerResult: profile.career_result || s.careerResult,
    }));
  }, [state.username]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        signup,
        logout,
        setCareerResult,
        setProfile,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
