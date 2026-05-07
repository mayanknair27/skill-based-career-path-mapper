const API_BASE = "http://localhost:8000";

// --- Types ---

export interface CareerResult {
  status: string;
  key: string;
  title: string;
  match_percentage: number;
  recommendation: string;
  reasoning: string;
  readiness_summary: string;
  expert_guidance: string;
  focus_area: string;
  next_action: string;
  pivot_summary: string | null;
  pivot_justification: string | null;
  missing_skills: string[];
  learned_skills: string[];
  updated_skills: string[];
  updated_experience_level: string;
  agent_observation: string | null;
  roadmap_labeled: RoadmapStep[];
  total_steps: number;
  resources: { name: string; url: string }[];
  career_skills: string[];
  thinking_trail: { name: string; detail: string; duration_ms: number }[];
  categorized_missing?: { skill: string; priority: string; reason: string }[];
  most_impactful_skill?: string;
  live_progress?: number;
}

export interface RoadmapStep {
  index: number;
  text: string;
  completed: boolean;
  id?: string;
}

export interface NetworkRole {
  title: string;
  match: number;
  r: number;
  theta: number;
  difficulty: string;
  salary: string;
  demand: number;
  missing: string[];
}

export interface UserProfile {
  career_goal?: string;
  experience_level?: string;
  current_skills?: string;
  career_result?: CareerResult;
  agent_state?: Record<string, unknown>;
  roadmap_progress?: Record<string, boolean>;
}

export interface AdminStats {
  total_users: number;
  logins_today: number;
  failed_today: number;
  total_signups: number;
}

export interface AuditEntry {
  username: string;
  event: string;
  timestamp: string;
}

// --- API Client ---

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// Auth
export async function apiLogin(username: string, password: string) {
  return apiFetch<{ status: string; message: string; username: string; profile: UserProfile }>(
    "/api/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) }
  );
}

export async function apiSignup(username: string, email: string, password: string) {
  return apiFetch<{ status: string; message: string }>(
    "/api/auth/signup",
    { method: "POST", body: JSON.stringify({ username, email, password }) }
  );
}



// Career
export async function apiProcessCareer(
  goal: string,
  skills: string,
  experience_level: string,
  username: string
) {
  return apiFetch<CareerResult>("/api/career/process", {
    method: "POST",
    body: JSON.stringify({ goal, skills, experience_level, username }),
  });
}

export async function apiGetNetwork(skills: string, exp: string) {
  const params = new URLSearchParams({ skills, exp });
  return apiFetch<{ careers: NetworkRole[] }>(`/api/career/network?${params}`);
}



// Profile
export async function apiGetProfile(username: string) {
  return apiFetch<UserProfile>(`/api/user/profile?username=${encodeURIComponent(username)}`);
}

export async function apiSaveProfile(username: string, profile_data: Record<string, unknown>) {
  return apiFetch<{ status: string }>("/api/user/profile", {
    method: "POST",
    body: JSON.stringify({ username, profile_data }),
  });
}

export async function apiCompleteMilestone(username: string, career_key: string, milestone_id: string) {
  return apiFetch<{ status: string }>("/api/user/milestone/complete", {
    method: "POST",
    body: JSON.stringify({ username, career_key, milestone_id }),
  });
}

// Admin
export async function apiGetAdminStats() {
  return apiFetch<AdminStats>("/api/admin/stats");
}

export async function apiGetAdminActivity(limit = 20) {
  return apiFetch<AuditEntry[]>(`/api/admin/activity?limit=${limit}`);
}
