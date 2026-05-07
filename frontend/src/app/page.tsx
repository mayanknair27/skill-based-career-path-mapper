"use client";

import { useAuth } from "@/context/auth-context";
import { AuthForm } from "@/components/auth-form";
import { InteractiveGlobe } from "@/components/interactive-globe";
import { DottedSurface } from "@/components/ui/dotted-surface";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  if (isAuthenticated) return null;

  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden px-4">
      {/* Interactive Three.js dotted surface background */}
      <DottedSurface />
      {/* Ambient background glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-[#7C3AED]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[#6366F1]/5 blur-[100px] pointer-events-none" />

      <div className="w-full max-w-6xl flex flex-col lg:flex-row items-center gap-8 lg:gap-16 relative z-10">
        {/* Left: Globe */}
        <div className="flex-1 flex items-center justify-center">
          <div className="relative">
            {/* Globe glow halo */}
            <div className="absolute inset-0 rounded-full bg-[#3B82F6]/5 blur-[60px] scale-110 pointer-events-none" />
            <InteractiveGlobe size={420} />
          </div>
        </div>

        {/* Right: Auth Form */}
        <div className="flex-1 w-full max-w-md">
          <AuthForm />
        </div>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#7C3AED]/30 to-transparent" />
    </main>
  );
}
