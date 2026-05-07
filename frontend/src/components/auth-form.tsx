"use client";

import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { Eye, EyeOff, Lock, User, Mail, ArrowRight, Sparkles } from "lucide-react";

type AuthView = "login" | "signup" | "forgot";

export function AuthForm() {
  const [view, setView] = useState<AuthView>("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Form fields
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const { login, signup } = useAuth();

  const resetForm = () => {
    setError("");
    setSuccess("");
    setUsername("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setShowPassword(false);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await signup(username, email, password);
      setSuccess("Account created! Redirecting to login...");
      setTimeout(() => {
        resetForm();
        setView("login");
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(124,58,237,0.3)] bg-[rgba(124,58,237,0.08)] px-4 py-1.5 text-xs text-[#A78BFA] mb-4">
          <Sparkles className="w-3.5 h-3.5" />
          <span className="font-semibold tracking-wider uppercase">Secure Access</span>
        </div>
        <h1 className="text-4xl font-bold text-gradient-violet mb-2 tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Career Mapper
        </h1>
        <p className="text-sm text-[#94A3B8]">
          {view === "login" && "Sign in to access your mission control"}
          {view === "signup" && "Create your pilot credentials"}
          {view === "forgot" && "Recover your access codes"}
        </p>
      </div>

      {/* Form Card */}
      <div className="glass-card p-8">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium">
            {success}
          </div>
        )}

        {view === "login" && (
          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="login-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Enter username"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Enter password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#A78BFA] transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-[#7C3AED] to-[#6366F1] text-white font-semibold rounded-xl hover:shadow-[0_0_30px_rgba(124,58,237,0.4)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Launch Mission <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {view === "signup" && (
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="signup-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Choose username"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="signup-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Enter email"
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="signup-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Choose password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#A78BFA] transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#A78BFA] uppercase tracking-wider">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
                <input
                  id="signup-confirm"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-[rgba(15,10,30,0.7)] border border-[rgba(124,58,237,0.2)] rounded-xl text-white text-sm focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED]/30 transition-all placeholder:text-[#475569]"
                  placeholder="Confirm password"
                  required
                />
              </div>
            </div>
            <button
              id="signup-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-[#7C3AED] to-[#6366F1] text-white font-semibold rounded-xl hover:shadow-[0_0_30px_rgba(124,58,237,0.4)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Create Account <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* Navigation links */}
        <div className="mt-6 flex items-center gap-3">
          {view === "login" && (
            <>
              <button
                onClick={() => { resetForm(); setView("signup"); }}
                className="flex-1 py-2.5 text-sm font-medium text-[#94A3B8] border border-[rgba(124,58,237,0.2)] rounded-xl hover:border-[#A78BFA] hover:text-white transition-all bg-transparent"
              >
                Create Account
              </button>
              <button
                onClick={() => { resetForm(); setView("forgot"); }}
                className="flex-1 py-2.5 text-sm font-medium text-[#94A3B8] border border-[rgba(124,58,237,0.2)] rounded-xl hover:border-[#A78BFA] hover:text-white transition-all bg-transparent"
              >
                Forgot Password
              </button>
            </>
          )}
          {(view === "signup" || view === "forgot") && (
            <button
              onClick={() => { resetForm(); setView("login"); }}
              className="w-full py-2.5 text-sm font-medium text-[#94A3B8] border border-[rgba(124,58,237,0.2)] rounded-xl hover:border-[#A78BFA] hover:text-white transition-all bg-transparent"
            >
              Back to Login
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
