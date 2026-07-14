"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { api, SpinResult, WheelSegment } from "@/lib/api";
import { Button, Logo } from "@/components/ui";
import Wheel from "@/components/Wheel";

function RuletaInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";

  const [segments, setSegments] = useState<WheelSegment[]>([]);
  const [estado, setEstado] = useState<"cargando" | "listo" | "invalido" | "usado">("cargando");
  const [nombre, setNombre] = useState<string | null>(null);
  const [error, setError] = useState("");

  const [spinning, setSpinning] = useState(false);
  const [target, setTarget] = useState<number | null>(null);
  const [result, setResult] = useState<SpinResult | null>(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    (async () => {
      if (!token) {
        setEstado("invalido");
        return;
      }
      try {
        const [cfg, magic] = await Promise.all([api.ruletaConfig(), api.validarMagic(token)]);
        setSegments(cfg);
        setNombre(magic.nombre);
        setEstado(magic.usado ? "usado" : "listo");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Enlace inválido.");
        setEstado("invalido");
      }
    })();
  }, [token]);

  async function girar() {
    if (spinning) return;
    setError("");
    setSpinning(true);
    try {
      const res = await api.girar(token);
      setResult(res);
      setTarget(res.segment_index);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo girar.");
      setSpinning(false);
    }
  }

  const onDone = useCallback(() => setShowResult(true), []);

  if (estado === "cargando") {
    return <Screen><p className="text-white/70">Cargando ruleta…</p></Screen>;
  }
  if (estado === "invalido") {
    return (
      <Screen>
        <div className="text-center">
          <p className="text-lg font-semibold text-white">Enlace inválido o expirado</p>
          <p className="mt-1 text-sm text-white/60">{error || "Regístrate para obtener tu enlace."}</p>
          <Link href="/registro" className="mt-4 inline-block font-semibold text-brand-yellow">
            Registrarme →
          </Link>
        </div>
      </Screen>
    );
  }
  if (estado === "usado") {
    return (
      <Screen>
        <div className="text-center">
          <div className="text-5xl">🎡</div>
          <p className="mt-3 text-lg font-semibold text-white">Ya usaste tu giro</p>
          <p className="mt-1 text-sm text-white/60">Cada participante puede girar una sola vez. ¡Gracias!</p>
        </div>
      </Screen>
    );
  }

  return (
    <Screen>
      <div className="w-full text-center">
        <h1 className="text-2xl font-extrabold text-white">
          {nombre ? `¡${nombre.split(" ")[0]}, gira y gana! ` : "¡Gira y gana!"}🏆
        </h1>
        <p className="mt-1 text-sm text-white/60">Toca el botón para girar la ruleta del equipo ganador.</p>

        <div className="my-8">
          <Wheel segments={segments} spinning={spinning} targetIndex={target} onDone={onDone} />
        </div>

        {error && <p className="mb-3 text-sm font-medium text-brand-red">{error}</p>}

        <Button variant="yellow" className="px-10 py-4 text-lg" onClick={girar} disabled={spinning}>
          {spinning ? "Girando…" : "🎯 ¡GIRAR!"}
        </Button>
      </div>

      <AnimatePresence>
        {showResult && result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-6 backdrop-blur"
          >
            <motion.div
              initial={{ scale: 0.8, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              className="w-full max-w-sm rounded-3xl bg-white p-8 text-center shadow-card"
            >
              <div className="text-6xl">{result.gano ? "🎉" : "🙌"}</div>
              <h2 className="mt-3 text-2xl font-extrabold text-navy">
                {result.gano ? "¡Ganaste!" : "¡Gracias por participar!"}
              </h2>
              {result.gano && result.prize_nombre && (
                <div className="my-4 rounded-2xl bg-navy p-4 text-xl font-extrabold text-brand-yellow">
                  {result.prize_nombre}
                </div>
              )}
              <p className="text-sm text-navy/70">{result.mensaje}</p>
              <Link href="/">
                <Button variant="primary" className="mt-6 w-full">Volver al inicio</Button>
              </Link>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Screen>
  );
}

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-stadium">
      <div className="mx-auto flex min-h-screen max-w-md flex-col items-center px-5 py-8">
        <div className="mb-4"><Logo dark /></div>
        <div className="flex flex-1 items-center">{children}</div>
      </div>
    </main>
  );
}

export default function RuletaPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-stadium" />}>
      <RuletaInner />
    </Suspense>
  );
}
