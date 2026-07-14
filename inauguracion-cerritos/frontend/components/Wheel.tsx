"use client";
import { motion, useAnimationControls } from "framer-motion";
import { useEffect, useState } from "react";
import { WheelSegment } from "@/lib/api";

const SIZE = 320;
const R = 150;
const CX = 160;
const CY = 160;

function pol(cx: number, cy: number, r: number, thetaDeg: number) {
  // theta medido en sentido horario desde el tope (12 en punto)
  const t = (thetaDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(t), y: cy - r * Math.cos(t) };
}

function slicePath(startDeg: number, endDeg: number) {
  const a = pol(CX, CY, R, startDeg);
  const b = pol(CX, CY, R, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${CX} ${CY} L ${a.x} ${a.y} A ${R} ${R} 0 ${large} 1 ${b.x} ${b.y} Z`;
}

function textPos(midDeg: number) {
  const p = pol(CX, CY, R * 0.62, midDeg);
  return { ...p, rot: midDeg };
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
      // 6 vueltas completas + alinear el centro del segmento al puntero (arriba)
      const target = 360 * 6 + (360 - center);
      controls
        .start({
          rotate: target,
          transition: { duration: 4.6, ease: [0.17, 0.67, 0.2, 1] },
        })
        .then(() => onDone());
    }
  }, [spinning, targetIndex, started, controls, seg, onDone]);

  return (
    <div className="relative mx-auto" style={{ width: SIZE, height: SIZE }}>
      {/* Puntero */}
      <div className="absolute left-1/2 top-[-6px] z-20 -translate-x-1/2">
        <div
          className="h-0 w-0 drop-shadow"
          style={{
            borderLeft: "14px solid transparent",
            borderRight: "14px solid transparent",
            borderTop: "26px solid #FFD200",
          }}
        />
      </div>

      {/* Aro exterior */}
      <div className="absolute inset-0 rounded-full pintuco-flame p-[6px] shadow-glow">
        <div className="h-full w-full rounded-full bg-navy-dark p-2">
          <motion.svg
            viewBox={`0 0 ${SIZE} ${SIZE}`}
            animate={controls}
            initial={{ rotate: 0 }}
            style={{ transformOrigin: "50% 50%" }}
            className="h-full w-full"
          >
            {segments.map((s, i) => {
              const start = i * seg;
              const end = (i + 1) * seg;
              const tp = textPos(start + seg / 2);
              return (
                <g key={s.id}>
                  <path d={slicePath(start, end)} fill={s.color} stroke="#071f3c" strokeWidth={1.5} />
                  <text
                    x={tp.x}
                    y={tp.y}
                    fill="#ffffff"
                    fontSize={n > 8 ? 9 : 11}
                    fontWeight={700}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    transform={`rotate(${tp.rot} ${tp.x} ${tp.y})`}
                  >
                    {s.nombre.length > 16 ? s.nombre.slice(0, 15) + "…" : s.nombre}
                  </text>
                </g>
              );
            })}
            <circle cx={CX} cy={CY} r={26} fill="#FFD200" stroke="#071f3c" strokeWidth={3} />
            <text x={CX} y={CY} fontSize={20} textAnchor="middle" dominantBaseline="middle">
              🏆
            </text>
          </motion.svg>
        </div>
      </div>
    </div>
  );
}
