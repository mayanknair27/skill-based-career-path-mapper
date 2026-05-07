"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle2, Circle, Loader2,
  AlertTriangle, ArrowUp, Shield,
  Cpu,
} from "lucide-react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
} from "recharts";

// ─── MetricCard ───

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  color?: string;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, subtext, color = "#A78BFA", icon }: MetricCardProps) {
  return (
    <div className="glass-card group">
      <div className="flex justify-between items-start">
        <div>
          <div className="text-[0.7rem] font-bold text-[#A78BFA] uppercase tracking-[0.15em] mb-2 opacity-80">
            {label}
          </div>
          <div className="text-3xl font-bold leading-none" style={{ color, textShadow: `0 0 20px ${color}33` }}>
            {value}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {icon && <div className="text-[#64748B] opacity-60">{icon}</div>}
          <div className="w-5 h-5 rounded-md opacity-30 group-hover:opacity-50 transition-opacity"
            style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
        </div>
      </div>
      {subtext && <div className="mt-3 text-[0.82rem] text-[#94A3B8] font-medium">{subtext}</div>}
    </div>
  );
}

// ─── SkillRadar ───

interface SkillRadarProps {
  careerSkills: string[];
  userSkills: string;
}

export function SkillRadar({ careerSkills, userSkills }: SkillRadarProps) {
  const userSkillSet = new Set(
    userSkills.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean)
  );
  const categories = careerSkills.slice(0, 6);
  const data = categories.map((skill) => ({
    subject: skill.charAt(0).toUpperCase() + skill.slice(1),
    user: userSkillSet.has(skill.toLowerCase()) ? 100 : 20,
    target: 100,
  }));

  return (
    <div className="glass-card h-full">
      <div className="text-[0.7rem] font-bold text-[#A78BFA] uppercase tracking-[0.15em] mb-2 opacity-80">
        Mastery Analysis
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data} cx="50%" cy="50%">
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "#94A3B8", fontSize: 10 }} />
          <Radar name="Target" dataKey="target" stroke="rgba(124, 58, 237, 0.2)" fill="rgba(124, 58, 237, 0.08)" />
          <Radar name="You" dataKey="user" stroke="#A78BFA" fill="rgba(167, 139, 250, 0.25)" strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── SkillGapCard ───

const RESOURCE_LINKS: Record<string, string> = {
  python: "https://www.python.org/about/gettingstarted/",
  html: "https://developer.mozilla.org/en-US/docs/Web/HTML",
  css: "https://developer.mozilla.org/en-US/docs/Web/CSS",
  javascript: "https://javascript.info/",
  react: "https://react.dev/",
  "node.js": "https://nodejs.org/en/learn/",
  sql: "https://www.w3schools.com/sql/",
  statistics: "https://www.khanacademy.org/math/statistics-probability",
  "machine learning": "https://www.coursera.org/learn/machine-learning",
};

interface SkillGapCardProps {
  skill: string;
  priority?: string;
  reason?: string;
}

export function SkillGapCard({ skill, priority = "Medium", reason }: SkillGapCardProps) {
  const priorityConfig = {
    High:   { color: "#EF4444", bg: "rgba(239,68,68,0.08)",  border: "rgba(239,68,68,0.2)",  icon: <AlertTriangle className="w-3.5 h-3.5" /> },
    Medium: { color: "#F59E0B", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.2)", icon: <ArrowUp className="w-3.5 h-3.5" /> },
    Low:    { color: "#10B981", bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.2)", icon: <Shield className="w-3.5 h-3.5" /> },
  };
  const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.Medium;
  const resourceUrl = RESOURCE_LINKS[skill.toLowerCase()];

  return (
    <div className="rounded-xl p-4 mb-2 transition-all duration-300 hover:translate-x-1"
      style={{ background: config.bg, border: `1px solid ${config.border}` }}>
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          {resourceUrl ? (
            <a href={resourceUrl} target="_blank" rel="noopener noreferrer"
              className="font-bold text-white hover:text-[#A78BFA] transition-colors text-sm">
              {skill.charAt(0).toUpperCase() + skill.slice(1)}
            </a>
          ) : (
            <span className="font-bold text-white text-sm">
              {skill.charAt(0).toUpperCase() + skill.slice(1)}
            </span>
          )}
        </div>
        <span className="flex items-center gap-1 text-[0.7rem] font-bold uppercase tracking-wider" style={{ color: config.color }}>
          {config.icon} {priority} Priority
        </span>
      </div>
      {reason && <p className="text-[#94A3B8] text-xs mt-2 leading-relaxed">{reason}</p>}
    </div>
  );
}

// ─── MilestoneCard ───

interface MilestoneCardProps {
  index: number;
  text: string;
  milestoneId: string;
  completed: boolean;
  onMastered: (text: string, milestoneId: string) => Promise<void>;
}

export function MilestoneCard({ index, text, milestoneId, completed, onMastered }: MilestoneCardProps) {
  const [loading, setLoading] = useState(false);

  const handleMastered = async () => {
    setLoading(true);
    try { await onMastered(text, milestoneId); }
    finally { setLoading(false); }
  };

  if (completed) {
    return (
      <div className="glass-card !border-emerald-500/20 !bg-emerald-500/5 mb-3 !p-5 opacity-70">
        <div className="flex items-start gap-4">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div className="flex-grow">
            <div className="text-[0.65rem] font-bold text-emerald-400 uppercase tracking-[0.15em] mb-1">
              Milestone {index} — Mastered
            </div>
            <div className="text-[#94A3B8] font-medium text-sm line-through">{text}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card mb-3 !p-5">
      <div className="flex items-start gap-4">
        <div className="w-3 h-3 rounded-full bg-[#7C3AED] mt-1.5 flex-shrink-0 animate-pulse-glow" style={{ color: "#7C3AED" }} />
        <div className="flex-grow">
          <div className="text-[0.65rem] font-bold text-[#A78BFA] uppercase tracking-[0.15em] mb-1">Milestone {index}</div>
          <div className="text-[#F8FAFC] font-semibold text-sm leading-relaxed">{text}</div>
        </div>
        <button onClick={handleMastered} disabled={loading}
          className="flex-shrink-0 px-4 py-2 text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-[#7C3AED] to-[#6366F1] text-white rounded-lg hover:shadow-[0_0_20px_rgba(124,58,237,0.4)] transition-all duration-300 disabled:opacity-50 flex items-center gap-1.5">
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Circle className="w-3.5 h-3.5" />}
          Mastered
        </button>
      </div>
    </div>
  );
}

// ─── AgentThinking ───

const STAGES = [
  "INITIALIZING — Mapping profile attributes...",
  "EVALUATING — Quantifying skill mastery...",
  "MATCHING — Correlating industry roles...",
  "GENERATING — Constructing actionable roadmap...",
  "FINALIZING — Synchronizing custom parameters...",
];

interface AgentThinkingProps {
  onComplete: () => void;
  visible: boolean;
}

export function AgentThinking({ onComplete, visible }: AgentThinkingProps) {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    if (!visible) { setCurrentStage(0); return; }
    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev >= STAGES.length - 1) {
          clearInterval(interval);
          setTimeout(onComplete, 400);
          return prev;
        }
        return prev + 1;
      });
    }, 500);
    return () => clearInterval(interval);
  }, [visible, onComplete]);

  if (!visible) return null;

  return (
    <div className="rounded-xl border border-[rgba(124,58,237,0.3)] bg-[rgba(124,58,237,0.06)] p-6 mb-6 animate-in fade-in duration-300">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-2.5 h-2.5 rounded-full bg-[#7C3AED] animate-pulse" />
        <Cpu className="w-4 h-4 text-[#C4B5FD]" />
        <span className="text-[#C4B5FD] font-bold text-xs uppercase tracking-[0.15em]">Processing Analysis Pipeline</span>
      </div>
      <div className="space-y-3">
        {STAGES.map((stage, i) => (
          <div key={i} className={`flex items-center gap-3 text-sm transition-all duration-300 ${i <= currentStage ? "opacity-100" : "opacity-30"}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border transition-all duration-300 ${
              i < currentStage ? "bg-[#7C3AED] border-[#7C3AED] text-white"
              : i === currentStage ? "border-[#A78BFA] text-[#A78BFA] animate-pulse"
              : "border-[#333] text-[#555]"
            }`}>
              {i < currentStage ? "✓" : i + 1}
            </div>
            <span className={i <= currentStage ? "text-white font-medium" : "text-[#555]"}>
              [{i + 1}/5] {stage}
            </span>
          </div>
        ))}
      </div>
      {currentStage >= STAGES.length - 1 && (
        <div className="mt-4 pt-3 border-t border-[rgba(124,58,237,0.15)]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-emerald-400 text-xs font-semibold">Analysis Complete — Rendering Results</span>
          </div>
        </div>
      )}
    </div>
  );
}
