"use client";

import { useEffect, useRef } from "react";

type MathItem = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  rot: number;
  size: number;
  alpha: number;
  type: "text" | "graph";
  text: string;
  graphVariant?: number; // 0-2 for different curve types
};

export default function MathBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Trigger animation on mount
    setTimeout(() => {
      if (canvas) {
        canvas.style.opacity = "0";
        canvas.style.transition = "opacity 3s ease-in-out";
        setTimeout(() => {
          canvas.style.opacity = "0.6";
        }, 50);
      }
    }, 100);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Respect reduced motion
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduceMotion) return;

    const SAFE = () => {
      // Avoid drawing behind hero area
      const w = window.innerWidth;
      const h = window.innerHeight;
      return { x: w * 0.25, y: h * 0.08, w: w * 0.5, h: h * 0.35 };
    };

    const items: MathItem[] = [];
    const glyphs = ["∑", "∫", "π", "√", "∞", "Δ", "θ", "λ", "≈", "≠", "≤", "≥"];
    const eqs = [
      "y=mx+b",
      "x²+y²=r²",
      "sin(x)",
      "f(x)",
      "a²+b²=c²",
      "log(x)",
      "e^x",
      "∂/∂x",
    ];
    const DPR = () => Math.max(1, Math.min(2, window.devicePixelRatio || 1));

    function resize() {
      if (!canvas || !ctx) return;
      const dpr = DPR();
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
      canvas.style.width = window.innerWidth + "px";
      canvas.style.height = window.innerHeight + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function rand(min: number, max: number) {
      return min + Math.random() * (max - min);
    }

    function inSafe(x: number, y: number) {
      const s = SAFE();
      return x > s.x && x < s.x + s.w && y > s.y && y < s.y + s.h;
    }

    function spawn(n = 40) {
      const w = window.innerWidth;
      const h = window.innerHeight;
      for (let i = 0; i < n; i++) {
        let x: number,
          y: number,
          tries = 0;
        do {
          x = rand(0, w);
          y = rand(0, h);
          tries++;
        } while (inSafe(x, y) && tries < 20);

        const kind = Math.random();
        items.push({
          x,
          y,
          vx: rand(-0.18, 0.18),
          vy: rand(-0.12, 0.12),
          r: rand(-0.002, 0.002),
          rot: rand(-0.2, 0.2),
          size: rand(35, 55),
          alpha: rand(0.15, 0.21),
          type: kind < 0.6 ? "text" : "graph",
          text:
            kind < 0.3
              ? glyphs[Math.floor(Math.random() * glyphs.length)]
              : eqs[Math.floor(Math.random() * eqs.length)],
          graphVariant: Math.floor(Math.random() * 3), // 0, 1, or 2
        });
      }
    }

    function drawGraph(
      x: number,
      y: number,
      size: number,
      a: number,
      variant: number = 0,
    ) {
      if (!ctx) return;
      ctx.save();
      ctx.translate(x, y);
      ctx.globalAlpha = a;
      ctx.lineWidth = 1;

      // simple axes
      ctx.beginPath();
      ctx.moveTo(-size * 1.2, 0);
      ctx.lineTo(size * 1.2, 0);
      ctx.moveTo(0, -size * 1.2);
      ctx.lineTo(0, size * 1.2);
      ctx.stroke();

      // different curve types
      ctx.beginPath();
      const step = 2;
      for (let t = -size * 0.8; t <= size * 0.8; t += step) {
        const px = t;
        let py = 0;

        if (variant === 0) {
          // parabola: y = x²
          py = -(t * t) / (size * 0.6);
        } else if (variant === 1) {
          // sine curve: y = sin(x)
          py = -Math.sin((t / size) * Math.PI * 1.5) * (size * 0.5);
        } else {
          // cubic: y = x³
          py = -(t * t * t) / (size * size * 0.15);
        }

        if (t === -size * 0.6) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
      ctx.restore();
    }

    resize();
    window.addEventListener("resize", resize, { passive: true });

    spawn(25);

    let animationId: number;

    function step() {
      if (!ctx) return;
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

      ctx.fillStyle = "rgba(0, 0, 0, 1)";
      ctx.strokeStyle = "rgba(0, 0, 0, 1)";
      ctx.font = "16px Indie Flower, cursive";

      const w = window.innerWidth;
      const h = window.innerHeight;

      for (const it of items) {
        it.x += it.vx;
        it.y += it.vy;
        it.rot += it.r;

        // wrap
        if (it.x < -50) it.x = w + 50;
        if (it.x > w + 50) it.x = -50;
        if (it.y < -50) it.y = h + 50;
        if (it.y > h + 50) it.y = -50;

        // Don't draw inside safe zone
        if (inSafe(it.x, it.y)) continue;

        if (it.type === "text") {
          ctx.save();
          ctx.translate(it.x, it.y);
          ctx.rotate(it.rot);
          ctx.globalAlpha = it.alpha;
          ctx.font = `${it.size}px Caveat, cursive`;
          ctx.fillText(it.text, 0, 0);
          ctx.restore();
        } else {
          drawGraph(it.x, it.y, it.size, it.alpha, it.graphVariant || 0);
        }
      }

      animationId = requestAnimationFrame(step);
    }

    step();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      id="math-bg"
      aria-hidden="true"
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{
        opacity: 0,
      }}
    />
  );
}
