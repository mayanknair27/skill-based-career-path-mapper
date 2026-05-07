"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  apiProcessCareer,
  apiGetNetwork,
  apiSaveProfile,
  apiCompleteMilestone,
  type CareerResult,
  type NetworkRole,
} from "@/lib/api";

import { Sidebar } from "@/components/dashboard/sidebar";
import { CareerNetwork } from "@/components/dashboard/career-network";
import { MetricCard, SkillRadar, MilestoneCard, SkillGapCard, AgentThinking } from "@/components/dashboard/cards";
import { AdminPanel } from "@/components/dashboard/admin-panel";

import {
  Zap,
  Brain,
  AlertTriangle as TriangleAlert,
  TrendingUp,
  BookOpen,
  ExternalLink,
} from "lucide-react";

const ADMIN_USERNAME = "MAK";

export default function DashboardPage() {
  const router = useRouter();
  const {
    isAuthenticated,
    username,
    careerResult,
    profile,
    setCareerResult,
    setProfile,
  } = useAuth();

  const [networkData, setNetworkData] = useState<NetworkRole[]>([]);
  const [processing, setProcessing] = useState(false);
  const [showThinking, setShowThinking] = useState(false);
  const [pendingAnalysis, setPendingAnalysis] = useState<{
    goal: string;
    skills: string;
    exp: string;
  } | null>(null);
  const [activeTab, setActiveTab] = useState<"map" | "analysis" | "roadmap">("map");

  // Redirect if not logged in
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);

  // Load galaxy data
  useEffect(() => {
    if (!isAuthenticated) return;
    const skills = profile.current_skills || "";
    const exp = profile.experience_level || "Beginner";
    apiGetNetwork(skills, exp)
      .then((res) => setNetworkData(res.careers))
      .catch(() => {});
  }, [isAuthenticated, profile.current_skills, profile.experience_level]);

  // Process career mission
  const startAnalysis = useCallback(
    async (goal: string, skills: string, exp: string) => {
      setPendingAnalysis({ goal, skills, exp });
      setShowThinking(true);
      setProcessing(true);
    },
    []
  );

  const onThinkingComplete = useCallback(async () => {
    if (!pendingAnalysis) return;
    const { goal, skills, exp } = pendingAnalysis;

    try {
      const result = await apiProcessCareer(goal, skills, exp, username);
      setCareerResult(result);
      setProfile({
        career_goal: goal,
        current_skills: skills,
        experience_level: exp,
        career_result: result,
      });

      // Persist to backend without agentState
      await apiSaveProfile(username, {
        career_goal: goal,
        experience_level: exp,
        current_skills: skills,
        career_result: result,
      });

      // Refresh network
      const networkRes = await apiGetNetwork(skills, exp);
      setNetworkData(networkRes.careers);
      setActiveTab("analysis");
    } catch (err) {
      console.error("Analysis failed:", err);
    } finally {
      setProcessing(false);
      setShowThinking(false);
      setPendingAnalysis(null);
    }
  }, [pendingAnalysis, username, setCareerResult, setProfile]);

  // Handle galaxy career selection
  const onSelectCareer = useCallback(
    async (title: string) => {
      const skills = profile.current_skills || "";
      const exp = profile.experience_level || "Beginner";
      startAnalysis(title, skills, exp);
    },
    [profile, startAnalysis]
  );

  const onMilestoneComplete = useCallback(
    async (text: string, milestoneId: string) => {
      // Find the career key from the active result
      const result = careerResult as CareerResult | null;
      if (!result?.key) return;

      // 1. Immediately save to backend database (Atomic)
      try {
        await apiCompleteMilestone(username, result.key, milestoneId);
      } catch (err) {
        console.error("Milestone atomic save failed:", err);
        return; // Halt if DB save fails
      }

      // 2. Fetch fresh career data to reflect completion and potential auto-rank-ups
      const goal = profile.career_goal || "";
      const skills = profile.current_skills || "";
      const exp = profile.experience_level || "Beginner";

      try {
        const updatedResult = await apiProcessCareer(goal, skills, exp, username);
        if (updatedResult.status === "success") {
          setCareerResult(updatedResult);
          setProfile((prevProfile) => {
            const nextProfile = {
              ...prevProfile,
              current_skills: updatedResult.updated_skills?.join(", "),
              experience_level: updatedResult.updated_experience_level
                ? updatedResult.updated_experience_level.charAt(0).toUpperCase() +
                  updatedResult.updated_experience_level.slice(1)
                : exp,
              career_result: updatedResult,
            };
            
            apiSaveProfile(username, {
              career_result: updatedResult,
              current_skills: nextProfile.current_skills,
              experience_level: nextProfile.experience_level,
            }).catch(console.error);

            return nextProfile;
          });
        }
      } catch (err) {
        console.error("Milestone sync failed:", err);
      }
    },
    [profile.career_goal, profile.current_skills, profile.experience_level, username, careerResult, setCareerResult, setProfile]
  );

  if (!isAuthenticated) return null;

  const result = careerResult as CareerResult | null;
  const currentSkills = profile.current_skills || "";
  const masteredSteps =
    result?.roadmap_labeled?.filter((s) => s.completed) || [];
  const activeSteps =
    result?.roadmap_labeled?.filter((s) => !s.completed) || [];
  const totalSteps = result?.total_steps || result?.roadmap_labeled?.length || 1;
  const progressPct = masteredSteps.length / Math.max(totalSteps, 1);

  return (
    <div className="flex min-h-screen">
      <Sidebar onInitiateMission={startAnalysis} loading={processing} />

      <main className="flex-1 overflow-y-auto p-8 lg:p-12">
        {/* Agent Thinking Animation */}
        <AgentThinking visible={showThinking} onComplete={onThinkingComplete} />

        {/* Tab Navigation */}
        {result && result.status === "success" && !showThinking && (
          <div className="flex flex-wrap items-center gap-2 mb-8 bg-[rgba(15,10,30,0.5)] p-1.5 rounded-xl border border-[rgba(124,58,237,0.15)] w-fit max-w-full">
            {(["map", "analysis", "roadmap"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 sm:px-6 py-2 rounded-lg text-xs sm:text-sm font-bold uppercase tracking-wider transition-all duration-300 ${
                  activeTab === tab
                    ? "bg-[#7C3AED] text-white shadow-[0_0_15px_rgba(124,58,237,0.4)]"
                    : "text-[#94A3B8] hover:text-white hover:bg-[rgba(124,58,237,0.1)]"
                }`}
              >
                {tab === "map" ? "Ecosystem Map" : tab === "analysis" ? "Skill Analysis" : "Action Roadmap"}
              </button>
            ))}
          </div>
        )}

        {!showThinking && (!result || result.status !== "success") && (
           <div className="mb-8">
            <CareerNetwork
              roles={networkData}
              currentTarget={profile.career_goal}
              onSelectRole={onSelectCareer}
            />
            {/* Placeholder state instead of "Awaiting Mission Parameters" */}
            <div className="mt-10 glass-card text-center py-12 border-dashed">
              <div className="text-[#A78BFA] text-4xl mb-4">◎</div>
              <h3
                className="text-lg font-bold text-white mb-2"
                style={{ fontFamily: "'Outfit', sans-serif" }}
              >
                Awaiting Profile Configuration
              </h3>
              <p className="text-[#94A3B8] text-sm max-w-md mx-auto">
                Select a destination in the Role Proximity Map or use the User Profile sidebar
                to configure your current skill set.
              </p>
            </div>
           </div>
        )}

        {!showThinking && result && result.status === "success" && (
          <div className="space-y-8">
            
            {/* Map Tab */}
            {activeTab === "map" && (
              <CareerNetwork
                roles={networkData}
                currentTarget={profile.career_goal}
                onSelectRole={onSelectCareer}
              />
            )}

            {/* Analysis Tab & Roadmap Tab Shared Status */}
            {(activeTab === "analysis" || activeTab === "roadmap") && (
              <div className="flex flex-col md:flex-row items-center justify-between rounded-xl border border-[rgba(124,58,237,0.2)] bg-[rgba(124,58,237,0.04)] px-6 py-4 gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#6EE7B7]" />
                  <span className="text-[#A78BFA] font-bold text-xs uppercase tracking-[0.1em]">
                    Career Blueprint Generated
                  </span>
                </div>
                <div className="text-sm text-[#94A3B8] font-medium">
                  Role: <b className="text-white">{result.title}</b> | Match:{" "}
                  <b className="text-white">{result.match_percentage}%</b> | Progress:{" "}
                  <b className="text-white">{Math.round(progressPct * 100)}%</b>
                </div>
              </div>
            )}

            {/* Analysis Tab */}
            {activeTab === "analysis" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Pivot Alert */}
                {result.pivot_summary && (
                  <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.06] px-6 py-5">
                    <div className="text-amber-400 font-bold text-xs uppercase tracking-[0.1em] mb-1">
                      Strategic Pivot Recommended
                    </div>
                    <div className="text-white text-lg font-bold mb-1">
                      {result.pivot_summary}
                    </div>
                    <div className="text-[#D1D5DB] text-sm leading-relaxed">
                      {result.pivot_justification}
                    </div>
                  </div>
                )}

                {/* Agent Observation */}
                {result.agent_observation && (
                  <div className="rounded-r-xl border-l-4 border-emerald-500 bg-emerald-500/[0.04] px-5 py-3">
                    <p className="text-emerald-400 text-sm font-semibold">
                      {result.agent_observation}
                    </p>
                  </div>
                )}

                {/* Metrics + Radar */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <MetricCard
                      label="Career Match"
                      value={`${result.match_percentage}%`}
                      subtext={result.readiness_summary || "In Progress"}
                      color="#A78BFA"
                      icon={<Zap className="w-5 h-5" />}
                    />
                    <MetricCard
                      label="Verified Skills"
                      value={currentSkills.split(",").filter(Boolean).length}
                      subtext="Core Foundations"
                      color="#10B981"
                      icon={<Brain className="w-5 h-5" />}
                    />
                    <MetricCard
                      label="Priority Gaps"
                      value={result.missing_skills?.length || 0}
                      subtext="Focus Areas"
                      color="#FCA5A5"
                      icon={<TriangleAlert className="w-5 h-5" />}
                    />
                  </div>
                  <SkillRadar
                    careerSkills={result.career_skills || []}
                    userSkills={currentSkills}
                  />
                </div>

                {/* Agent Decision Log */}
                <div className="glass-card">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#A78BFA] blur-[2px]" />
                    <span className="text-[#A78BFA] text-[0.7rem] font-bold uppercase tracking-[0.1em]">
                      Recommendation Details
                    </span>
                  </div>
                  <h4 className="text-xl font-bold text-white mb-3">
                    {result.recommendation || result.title}
                  </h4>
                  <p className="text-[#94A3B8] text-sm leading-relaxed mb-4">
                    {result.expert_guidance}
                  </p>
                  <div className="pt-3 border-t border-[rgba(167,139,250,0.1)] text-[#A78BFA] text-sm italic">
                    &quot;Based on your profile, I recommend focusing on{" "}
                    {result.most_impactful_skill || "foundational skills"} to
                    maximize your growth trajectory.&quot;
                  </div>
                </div>
              </div>
            )}

            {/* Roadmap Tab */}
            {activeTab === "roadmap" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                
                {/* Skill Gaps */}
                <div>
                  <h3
                    className="text-xl font-bold text-white mb-4"
                    style={{ fontFamily: "'Outfit', sans-serif" }}
                  >
                    Skill Gap Analysis
                  </h3>
                  {result.categorized_missing?.length ? (
                    result.categorized_missing.map((item, i) => (
                      <SkillGapCard
                        key={i}
                        skill={item.skill}
                        priority={item.priority}
                        reason={item.reason}
                      />
                    ))
                  ) : result.missing_skills?.length ? (
                    result.missing_skills.map((skill, i) => (
                      <SkillGapCard key={i} skill={skill} />
                    ))
                  ) : (
                    <div className="glass-card text-center text-emerald-400 font-semibold text-sm py-6">
                      No critical skill gaps detected. You are ready!
                    </div>
                  )}
                </div>

                {/* Roadmap */}
                <div>
                  <div className="text-[0.7rem] font-bold text-[#A78BFA] uppercase tracking-[0.15em] mb-2">
                    Actionable Progression
                  </div>
                  <p className="text-[#38BDF8] font-semibold text-sm mb-2">
                    {Math.round(progressPct * 100)}% Complete ({masteredSteps.length}/
                    {totalSteps} steps)
                  </p>
                  {/* Progress bar */}
                  <div className="w-full h-2 rounded-full bg-[rgba(15,10,30,0.7)] mb-6 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#38BDF8] transition-all duration-700"
                      style={{ width: `${progressPct * 100}%` }}
                    />
                  </div>

                  {activeSteps.length === 0 && masteredSteps.length > 0 ? (
                    <div className="glass-card text-center text-emerald-400 font-semibold text-sm py-6">
                      All current milestones mastered. Readiness level achieved!
                    </div>
                  ) : (
                    activeSteps.map((step) => (
                      <MilestoneCard
                        key={step.index}
                        index={step.index}
                        text={step.text}
                        milestoneId={step.id || `ms_${username}_${result.title}_${step.index}`}
                        completed={false}
                        onMastered={onMilestoneComplete}
                      />
                    ))
                  )}

                  {masteredSteps.length > 0 && (
                    <details className="mt-4 group">
                      <summary className="cursor-pointer text-sm font-semibold text-[#94A3B8] hover:text-white transition-colors flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        Completed Milestones ({masteredSteps.length})
                      </summary>
                      <div className="mt-3 space-y-0">
                        {masteredSteps.map((step) => (
                          <MilestoneCard
                            key={step.index}
                            index={step.index}
                            text={step.text}
                            milestoneId={step.id || `ms_${username}_${result.title}_${step.index}`}
                            completed={true}
                            onMastered={onMilestoneComplete}
                          />
                        ))}
                      </div>
                    </details>
                  )}
                </div>

                {/* Resources */}
                {result.resources?.length > 0 && (
                  <div>
                    <h3
                      className="text-xl font-bold text-white mb-4"
                      style={{ fontFamily: "'Outfit', sans-serif" }}
                    >
                      <BookOpen className="w-5 h-5 inline mr-2 text-[#A78BFA]" />
                      Learning Resources
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {result.resources.map((res, i) => (
                        <a
                          key={i}
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="glass-card !p-4 flex items-center justify-between group hover:!border-[#A78BFA]/50"
                        >
                          <span className="text-white font-semibold text-sm">
                            {res.name}
                          </span>
                          <ExternalLink className="w-4 h-4 text-[#64748B] group-hover:text-[#A78BFA] transition-colors" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
                
              </div>
            )}
            
            {/* Admin Panel */}
            {username === ADMIN_USERNAME && <AdminPanel />}
          </div>
        )}
      </main>
    </div>
  );
}
