"use client";

import { useEffect, useState } from "react";
import { apiGetAdminStats, apiGetAdminActivity } from "@/lib/api";
import type { AdminStats, AuditEntry } from "@/lib/api";
import { Shield, Users, LogIn, AlertTriangle, UserPlus } from "lucide-react";

export function AdminPanel() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [activity, setActivity] = useState<AuditEntry[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    (async () => {
      try {
        const [s, a] = await Promise.all([apiGetAdminStats(), apiGetAdminActivity(20)]);
        setStats(s);
        setActivity(a);
      } catch {
        // silently fail for non-admin users
      }
    })();
  }, [expanded]);

  return (
    <div className="mt-16">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-5 py-4 rounded-xl border border-[rgba(124,58,237,0.15)] bg-[rgba(124,58,237,0.03)] hover:bg-[rgba(124,58,237,0.06)] transition-all text-[#94A3B8] hover:text-white"
      >
        <Shield className="w-4 h-4 text-[#A78BFA]" />
        <span className="font-semibold text-sm">Admin System Terminal</span>
        <span className={`ml-auto transition-transform ${expanded ? "rotate-180" : ""}`}>▾</span>
      </button>

      {expanded && stats && (
        <div className="mt-4 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <h3 className="text-lg font-bold text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Security & Audit Panel
          </h3>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Users", value: stats.total_users, icon: <Users className="w-4 h-4" />, color: "#A78BFA" },
              { label: "Logins", value: stats.logins_today, icon: <LogIn className="w-4 h-4" />, color: "#10B981" },
              { label: "Failures", value: stats.failed_today, icon: <AlertTriangle className="w-4 h-4" />, color: "#EF4444" },
              { label: "Signups", value: stats.total_signups, icon: <UserPlus className="w-4 h-4" />, color: "#3B82F6" },
            ].map((item) => (
              <div key={item.label} className="glass-card !p-4 text-center">
                <div className="flex items-center justify-center mb-2" style={{ color: item.color }}>
                  {item.icon}
                </div>
                <div className="text-2xl font-bold text-white">{item.value}</div>
                <div className="text-xs text-[#94A3B8] mt-1">{item.label}</div>
              </div>
            ))}
          </div>

          {/* Activity Table */}
          <div className="glass-card !p-0 overflow-hidden">
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[rgba(124,58,237,0.15)]">
                    <th className="text-left py-3 px-4 text-xs font-bold text-[#A78BFA] uppercase tracking-wider">User</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-[#A78BFA] uppercase tracking-wider">Event</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-[#A78BFA] uppercase tracking-wider">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((entry, i) => (
                    <tr key={i} className="border-b border-[rgba(255,255,255,0.03)] hover:bg-[rgba(124,58,237,0.03)] transition-colors">
                      <td className="py-2.5 px-4 text-white font-medium">{entry.username}</td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                            entry.event === "LOGIN_FAILED"
                              ? "bg-red-500/10 text-red-400"
                              : entry.event === "SIGNUP"
                              ? "bg-blue-500/10 text-blue-400"
                              : "bg-emerald-500/10 text-emerald-400"
                          }`}
                        >
                          {entry.event}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-[#64748B] text-xs">{entry.timestamp}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
