"use client";
import { motion, useAnimationControls } from "framer-motion";
import { useEffect, useState } from "react";
import { WheelSegment } from "@/lib/api";

const VIEW = 420;
const CX = 210;
const CY = 210;
const R = 196; // radio de los segmentos
const BULBS = 24;

function pol(cx: number, cy: number, r: number, thetaDeg: number) {
  const t = (thetaDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(t), y: cy - r * Math.cos(t) };
}

function slicePath(startDeg: number, endDeg: number, r: number) {
  const a = pol(CX, CY, r, startDeg);
  const b = pol(CX, CY, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${CX} ${CY} L ${a.x} ${a.y} A ${r} ${r} 0 ${large} 1 ${b.x} ${b.y} Z`;
}

// Aclara/oscurece un color hex para crear degradados por segmento
function shade(hex: string, pct: number) {
  const h = hex.replace("#", "");
  if (h.length !== 6) return hex;
  const num = parseInt(h, 16);
  let r = (num >> 16) + Math.round(255 * pct);
  let g = ((num >> 8) & 0xff) + Math.round(255 * pct);
  let b = (num & 0xff) + Math.round(255 * pct);
  r = Math.max(0, Math.min(255, r));
  g = Math.max(0, Math.min(255, g));
  b = Math.max(0, Math.min(255, b));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

export default function Wheel({
  segments,
  spinning,
  targetIndex,
  onDone,
}: {
  segments: WheelSegment[];
  spinning: boolean;
  targetIndex: number | null;
  onDone: () => void;
}) {
  const controls = useAnimationControls();
  const [started, setStarted] = useState(false);
  const n = segments.length || 1;
  const seg = 360 / n;

  useEffect(() => {
    if (spinning && targetIndex !== null && !started) {
      setStarted(true);
      const center = (targetIndex + 0.5) * seg;
      const target = 360 * 8 + (360 - center); // 8 vueltas + alinear al puntero
      controls
        .start({
          rotate: target,
          transition: { duration: 5.2, ease: [0.16, 0.72, 0.14, 1] },
        })
        .then(() => onDone());
    }
  }, [spinning, targetIndex, started, controls, seg, onDone]);

  return (
    <div
      className="relative mx-auto wheel-glow"
      style={{
        width: "min(88vw, 420px)",
        aspectRatio: "1",
        animation: spinning ? "none" : "idleFloat 3.5s ease-in-out infinite",
      }}
    >
      {/* Puntero superior */}
      <div className="absolute left-1/2 top-[-10px] z-30 -translate-x-1/2">
        <svg width="52" height="58" viewBox="0 0 52 58">
          <defs>
            <linearGradient id="ptr" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#FFE680" />
              <stop offset="0.5" stopColor="#FFD200" />
              <stop offset="1" stopColor="#E6A700" />
            </linearGradient>
          </defs>
          <path d="M26 54 L6 14 Q26 2 46 14 Z" fill="url(#ptr)" stroke="#0A2E57" strokeWidth="3" strokeLinejoin="round" />
          <circle cx="26" cy="16" r="6" fill="#0A2E57" />
        </svg>
      </div>

      <svg viewBox={`0 0 ${VIEW} ${VIEW}`} className="h-full w-full">
        <defs>
          <radialGradient id="gloss" cx="0.5" cy="0.35" r="0.75">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.35" />
            <stop offset="0.45" stopColor="#ffffff" stopOpacity="0.06" />
            <stop offset="1" stopColor="#000000" stopOpacity="0.18" />
          </radialGradient>
          <radialGradient id="rim" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0.86" stopColor="#12386b" />
            <stop offset="0.9" stopColor="#FFD200" />
            <stop offset="0.95" stopColor="#E63329" />
            <stop offset="1" stopColor="#7A2E8E" />
          </radialGradient>
          <radialGradient id="hub" cx="0.5" cy="0.4" r="0.6">
            <stop offset="0" stopColor="#FFF1B0" />
            <stop offset="0.6" stopColor="#FFD200" />
            <stop offset="1" stopColor="#E6A700" />
          </radialGradient>
        </defs>

        {/* Aro exterior con degradado marca */}
        <circle cx={CX} cy={CY} r={R + 12} fill="url(#rim)" />
        <circle cx={CX} cy={CY} r={R + 4} fill="#071f3c" />

        {/* Bombillos alrededor */}
        {Array.from({ length: BULBS }).map((_, i) => {
          const p = pol(CX, CY, R + 8, (360 / BULBS) * i);
          return (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r={4.2}
              fill="#FFF3B0"
              style={{ animation: `bulbpulse 1s ease-in-out ${(i % 4) * 0.25}s infinite` }}
            />
          );
        })}

        {/* Disco giratorio */}
        <motion.g animate={controls} initial={{ rotate: 0 }} style={{ transformOrigin: "50% 50%" }}>
          {segments.map((s, i) => {
            const start = i * seg;
            const end = (i + 1) * seg;
            const mid = start + seg / 2;
            const tp = pol(CX, CY, R * 0.64, mid);
            let rot = mid;
            if (mid > 90 && mid < 270) rot += 180; // texto siempre legible
            const gid = `seg${i}`;
            return (
              <g key={s.id}>
                <defs>
                  <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor={shade(s.color, 0.18)} />
                    <stop offset="1" stopColor={shade(s.color, -0.12)} />
                  </linearGradient>
                </defs>
                <path d={slicePath(start, end, R)} fill={`url(#${gid})`} stroke="#ffffff" strokeWidth={2.5} />
                <text
                  x={tp.x}
                  y={tp.y}
                  fill="#ffffff"
                  fontSize={n > 8 ? 12 : 15}
                  fontWeight={800}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  transform={`rotate(${rot} ${tp.x} ${tp.y})`}
                  style={{ paintOrder: "stroke", stroke: "rgba(0,0,0,0.28)", strokeWidth: 3 }}
                >
                  {s.nombre.length > 15 ? s.nombre.slice(0, 14) + "…" : s.nombre}
                </text>
              </g>
            );
          })}
          {/* Brillo glossy encima */}
          <circle cx={CX} cy={CY} r={R} fill="url(#gloss)" pointerEvents="none" />
        </motion.g>

        {/* Centro / hub dorado */}
        <circle cx={CX} cy={CY} r={44} fill="#071f3c" />
        <circle cx={CX} cy={CY} r={38} fill="url(#hub)" stroke="#071f3c" strokeWidth={3} />
        <text x={CX} y={CY + 1} fontSize={34} textAnchor="middle" dominantBaseline="middle">
          🏆
        </text>
      </svg>
    </div>
  );
}
