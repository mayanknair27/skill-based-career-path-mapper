"use client";

import { useEffect, useRef, useCallback } from "react";
import type { NetworkRole } from "@/lib/api";

interface CareerNetworkProps {
  roles: NetworkRole[];
  currentTarget?: string;
  onSelectRole: (title: string) => void;
}

export function CareerNetwork({ roles, currentTarget, onSelectRole }: CareerNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hoveredRef = useRef<string | null>(null);
  const animRef = useRef<number>(0);
  const timeRef = useRef(0);
  const rolesRef = useRef(roles);
  rolesRef.current = roles;

  const toCanvas = useCallback(
    (r: number, theta: number, cx: number, cy: number, scale: number): [number, number] => {
      const rad = (theta * Math.PI) / 180;
      return [cx + r * scale * Math.cos(rad), cy + r * scale * Math.sin(rad)];
    },
    []
  );

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);

    const cx = w / 2;
    const cy = h / 2;
    const scale = Math.min(w, h) / 240;

    timeRef.current += 0.005; // slightly slower for professional feel
    const t = timeRef.current;

    ctx.clearRect(0, 0, w, h);

    // 1. Draw subtle background grid/crosshairs
    ctx.strokeStyle = "rgba(124,58,237,0.03)";
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = (cx % gridSize); x < w; x += gridSize) {
      for (let y = (cy % gridSize); y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x - 2, y);
        ctx.lineTo(x + 2, y);
        ctx.moveTo(x, y - 2);
        ctx.lineTo(x, y + 2);
        ctx.stroke();
      }
    }

    const data = rolesRef.current;
    if (!data.length) return;

    // Calculate node coordinates
    const nodes = data.map((d) => {
      const [nx, ny] = toCanvas(d.r, d.theta, cx, cy, scale);
      return { ...d, x: nx, y: ny };
    });

    // 2. Draw Network Mesh (connect nearby nodes)
    ctx.lineWidth = 1;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const n1 = nodes[i];
        const n2 = nodes[j];
        const dist = Math.hypot(n1.x - n2.x, n1.y - n2.y);
        const maxDist = 120 * scale;
        
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.15;
          ctx.beginPath();
          ctx.moveTo(n1.x, n1.y);
          ctx.lineTo(n2.x, n2.y);
          ctx.strokeStyle = `rgba(167, 139, 250, ${alpha})`;
          ctx.stroke();
        }
      }
      
      // Connection back to core (user)
      const distToCore = Math.hypot(nodes[i].x - cx, nodes[i].y - cy);
      const alphaCore = Math.max(0, 0.1 - distToCore / (300 * scale));
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(nodes[i].x, nodes[i].y);
      ctx.strokeStyle = `rgba(99, 102, 241, ${alphaCore})`;
      ctx.setLineDash([2, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 3. Highlight current target path
    if (currentTarget) {
      const target = nodes.find((d) => d.title.toLowerCase() === currentTarget.toLowerCase());
      if (target) {
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        
        // Let's make the line pulse
        const pulseAlpha = Math.sin(t * 3) * 0.3 + 0.6;
        
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(252, 211, 77, ${pulseAlpha})`; // amber-300
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Data particles flowing to target
        const numParticles = 3;
        for (let i = 0; i < numParticles; i++) {
          const pt = (t * 1.5 + i / numParticles) % 1;
          const px = cx + (target.x - cx) * pt;
          const py = cy + (target.y - cy) * pt;
          
          ctx.beginPath();
          ctx.arc(px, py, 2, 0, Math.PI * 2);
          ctx.fillStyle = "#FCD34D";
          ctx.fill();
        }
      }
    }

    // 4. Draw Nodes
    nodes.forEach((d) => {
      const isHovered = hoveredRef.current === d.title;
      const isTarget = d.title.toLowerCase() === currentTarget?.toLowerCase();

      // Professional colors: Emerald (High match), Blue (Med match), Violet (Default)
      let color = "124, 58, 237"; // #7C3AED
      if (d.match > 75) color = "16, 185, 129"; // #10B981
      else if (d.match > 40) color = "59, 130, 246"; // #3B82F6
      if (isTarget) color = "245, 158, 11"; // #F59E0B

      const nodeSize = 6;
      
      // Node Outer Ring (Hexagon)
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI) / 3 + t * 0.2; // Slow rotation
        const hx = d.x + (nodeSize + (isHovered ? 6 : 4)) * Math.cos(angle);
        const hy = d.y + (nodeSize + (isHovered ? 6 : 4)) * Math.sin(angle);
        if (i === 0) ctx.moveTo(hx, hy);
        else ctx.lineTo(hx, hy);
      }
      ctx.closePath();
      ctx.strokeStyle = `rgba(${color}, ${isHovered || isTarget ? 0.8 : 0.4})`;
      ctx.lineWidth = isHovered ? 1.5 : 1;
      ctx.stroke();
      if (isHovered) {
        ctx.fillStyle = `rgba(${color}, 0.1)`;
        ctx.fill();
      }

      // Node Core (Square or Circle)
      ctx.beginPath();
      ctx.arc(d.x, d.y, isHovered ? 3 : 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgb(${color})`;
      ctx.shadowColor = `rgb(${color})`;
      ctx.shadowBlur = isHovered ? 15 : 5;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Label Dataviz styling
      ctx.font = `${isHovered ? "bold 11px" : "10px"} 'Inter', system-ui, sans-serif`;
      ctx.fillStyle = isHovered ? "#FFFFFF" : "rgba(203, 213, 225, 0.8)"; // slate-300
      ctx.textAlign = "center";
      ctx.fillText(d.title, d.x, d.y - nodeSize - 10);

      if (isHovered) {
        // Render sleek data box
        const textW = ctx.measureText(`${d.match}% Match`).width;
        const boxW = textW + 16;
        const boxH = 18;
        
        ctx.fillStyle = "rgba(15, 10, 30, 0.9)";
        ctx.strokeStyle = `rgba(${color}, 0.5)`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(d.x - boxW/2, d.y + nodeSize + 8, boxW, boxH, 4);
        ctx.fill();
        ctx.stroke();
        
        ctx.font = "bold 9px 'Inter', system-ui, sans-serif";
        ctx.fillStyle = `rgb(${color})`;
        ctx.fillText(`${d.match}% Match`, d.x, d.y + nodeSize + 20);
      }
    });

    // 5. Draw Central Core (User)
    ctx.save();
    const corePulse = Math.sin(t * 2) * 2 + 8;
    
    // Core structural ring
    ctx.beginPath();
    ctx.arc(cx, cy, corePulse + 6, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(99, 102, 241, 0.3)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.lineDashOffset = -t * 10;
    ctx.stroke();
    
    // Core solid
    ctx.beginPath();
    ctx.arc(cx, cy, corePulse, 0, Math.PI * 2);
    const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, corePulse);
    coreGrad.addColorStop(0, "#FFFFFF");
    coreGrad.addColorStop(0.3, "#818CF8"); // indigo-400
    coreGrad.addColorStop(1, "#4F46E5"); // indigo-600
    ctx.fillStyle = coreGrad;
    ctx.shadowColor = "#6366F1";
    ctx.shadowBlur = 20;
    ctx.fill();
    ctx.restore();

    // Central Label
    ctx.font = "bold 9px 'Inter', system-ui, sans-serif";
    ctx.fillStyle = "#A5B4FC"; // indigo-300
    ctx.textAlign = "center";
    ctx.letterSpacing = "2px";
    ctx.fillText("CURRENT", cx, cy + corePulse + 18);
    ctx.fillText("SKILLS", cx, cy + corePulse + 28);

    animRef.current = requestAnimationFrame(draw);
  }, [currentTarget, toCanvas]);

  useEffect(() => {
    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [draw]);

  // Hit testing
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const cx = w / 2;
      const cy = h / 2;
      const scale = Math.min(w, h) / 240;

      let found: string | null = null;
      for (const d of rolesRef.current) {
        const [px, py] = toCanvas(d.r, d.theta, cx, cy, scale);
        const dist = Math.sqrt((mx - px) ** 2 + (my - py) ** 2);
        if (dist < 15) {
          found = d.title;
          break;
        }
      }
      hoveredRef.current = found;
      canvas.style.cursor = found ? "pointer" : "crosshair";
    },
    [toCanvas]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const cx = w / 2;
      const cy = h / 2;
      const scale = Math.min(w, h) / 240;

      for (const d of rolesRef.current) {
        const [px, py] = toCanvas(d.r, d.theta, cx, cy, scale);
        const dist = Math.sqrt((mx - px) ** 2 + (my - py) ** 2);
        if (dist < 15) {
          onSelectRole(d.title);
          break;
        }
      }
    },
    [onSelectRole, toCanvas]
  );

  return (
    <div>
      <div className="text-center mb-5">
        <div className="text-[0.7rem] font-bold text-[#A78BFA] uppercase tracking-[0.2em]">
          Career Ecosystem
        </div>
        <h2 className="text-2xl font-bold text-white mt-1" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Role Proximity Map
        </h2>
        <p className="text-sm text-[#94A3B8] mt-1">
          Roles mapped to your current skillset — A structural visualization of career transitions.
        </p>
      </div>
      <div className="glass-card p-0 overflow-hidden relative">
        {/* Subtle grid background applied via CSS */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-30 pointer-events-none" />
        <canvas
          ref={canvasRef}
          className="w-full"
          style={{ height: 500 }}
          onMouseMove={handleMouseMove}
          onClick={handleClick}
        />
      </div>
    </div>
  );
}
