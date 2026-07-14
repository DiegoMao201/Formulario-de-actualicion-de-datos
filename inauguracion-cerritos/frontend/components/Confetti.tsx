"use client";
import { useMemo } from "react";

const COLORS = ["#FFD200", "#E63329", "#1F9E5A", "#1F8BD6", "#7A2E8E", "#FF8A00", "#ffffff"];

/** Confeti CSS ligero (sin dependencias). Se monta cuando `active` es true. */
export default function Confetti({ active, pieces = 90 }: { active: boolean; pieces?: number }) {
  const items = useMemo(
    () =>
      Array.from({ length: pieces }).map((_, i) => ({
        left: Math.random() * 100,
        delay: Math.random() * 0.6,
        duration: 2.4 + Math.random() * 2.2,
        color: COLORS[i % COLORS.length],
        size: 7 + Math.random() * 8,
        round: Math.random() > 0.6,
      })),
    [pieces]
  );

  if (!active) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[60] overflow-hidden">
      {items.map((p, i) => (
        <span
          key={i}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.round ? p.size : p.size * 1.4,
            borderRadius: p.round ? "50%" : "2px",
            background: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
          }}
        />
      ))}
    </div>
  );
}
