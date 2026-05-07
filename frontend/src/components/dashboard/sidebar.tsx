"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/auth-context";
import {
  LogOut,
  Target,
  Gauge,
  Wrench,
  Play,
  ChevronDown,
  Settings,
} from "lucide-react";

interface SidebarProps {
  onInitiateMission: (goal: string, skills: string, exp: string) => void;
  loading: boolean;
}

const EXP_LEVELS = ["Beginner", "Intermediate", "Advanced"];

export function Sidebar({ onInitiateMission, loading }: SidebarProps) {
  const { username, profile, logout } = useAuth();

  const [goal, setGoal] = useState(profile.career_goal || "");
  const [skills, setSkills] = useState(profile.current_skills || "");
  const [exp, setExp] = useState(profile.experience_level || "Beginner");
  const [expOpen, setExpOpen] = useState(false);

  useEffect(() => {
    if (profile.career_goal) setGoal(profile.career_goal);
    if (profile.current_skills) setSkills(profile.current_skills);
    if (profile.experience_level) setExp(profile.experience_level);
  }, [profile.career_goal, profile.current_skills, profile.experience_level]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    onInitiateMission(goal, skills, exp);
  };

  return (
    <aside className="w-80 min-h-screen flex flex-col border-r border-[rgba(124,58,237,0.15)] bg-[#0d0a1a]/90 backdrop-blur-xl">
      {/* Profile Header */}
      <div className="p-6 border-b border-[rgba(124,58,237,0.1)]">
        <h1
          className="text-xl font-bold text-gradient-violet mb-1"
          style={{ fontFamily: "'Outfit', sans-serif" }}
        >
          User Profile
        </h1>
        <div className="flex items-center gap-3 mt-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#7C3AED] via-[#8B5CF6] to-[#6366F1] flex items-center justify-center text-white text-sm font-bold shadow-[0_0_15px_rgba(124,58,237,0.4)]">
            {username.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-bold text-white tracking-wide">{username}</p>
            <p className="text-xs text-[#94A3B8] font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_#10B981]"></span>
              Online
            </p>
          </div>
        </div>
      </div>

      {/* Config Form */}
      <form onSubmit={handleSubmit} className="flex-1 p-6 space-y-5">
        <div className="flex items-center gap-2 text-[0.7rem] font-bold text-[#A78BFA] uppercase tracking-[0.2em] mb-1">
          <Settings className="w-3.5 h-3.5" />
          Configuration
        </div>

        {/* Desired Role */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-semibold text-[#94A3B8]">
            <Target className="w-3.5 h-3.5" /> Desired Role
          </label>
          <input
            id="config-role"
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Data Scientist"
            className="w-full px-3 py-2.5 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-lg text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
          />
        </div>

        {/* Experience Level */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-semibold text-[#94A3B8]">
            <Gauge className="w-3.5 h-3.5" /> Experience Level
          </label>
          <div className="relative">
            <button
              type="button"
              onClick={() => setExpOpen(!expOpen)}
              className="w-full px-3 py-2.5 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-lg text-white text-sm text-left flex items-center justify-between focus:border-[#7C3AED] focus:outline-none transition-all"
            >
              {exp}
              <ChevronDown className={`w-4 h-4 text-[#64748B] transition-transform ${expOpen ? "rotate-180" : ""}`} />
            </button>
            {expOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#120e26] border border-[rgba(124,58,237,0.3)] rounded-lg overflow-hidden z-50 shadow-2xl">
                {EXP_LEVELS.map((level) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => {
                      setExp(level);
                      setExpOpen(false);
                    }}
                    className={`w-full px-3 py-2.5 text-left text-sm hover:bg-[rgba(124,58,237,0.1)] transition-colors ${
                      exp === level ? "text-[#A78BFA] font-semibold bg-[rgba(124,58,237,0.05)]" : "text-[#94A3B8]"
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Current Skills */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-semibold text-[#94A3B8]">
            <Wrench className="w-3.5 h-3.5" /> Current Skills
          </label>
          <textarea
            id="config-skills"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder="python, sql, javascript..."
            rows={3}
            className="w-full px-3 py-2.5 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-lg text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569] resize-none"
          />
        </div>

        {/* Submit */}
        <button
          id="generate-roadmap"
          type="submit"
          disabled={loading || !goal.trim()}
          className="w-full py-3.5 bg-gradient-to-r from-[#7C3AED] via-[#8B5CF6] to-[#6366F1] text-white font-bold tracking-wide rounded-xl hover:shadow-[0_0_40px_rgba(124,58,237,0.6)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              <Play className="w-4 h-4" fill="currentColor" />
              Generate Roadmap
            </>
          )}
        </button>
      </form>

      {/* Logout */}
      <div className="p-6 border-t border-[rgba(124,58,237,0.1)]">
        <button
          onClick={logout}
          className="w-full py-2.5 text-sm font-medium text-[#94A3B8] border border-[rgba(124,58,237,0.2)] rounded-xl hover:border-red-500/30 hover:text-red-400 transition-all bg-transparent flex items-center justify-center gap-2"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
