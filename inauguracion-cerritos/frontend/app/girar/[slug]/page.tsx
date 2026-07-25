"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { api, ChannelPublic, SpinResult, WheelSegment } from "@/lib/api";
import { Button, Card, Input, Logo } from "@/components/ui";
import Wheel from "@/components/Wheel";
import Confetti from "@/components/Confetti";

export default function GirarCanalPage() {
  const params = useParams();
  const slug = String(params?.slug || "");

  const [canal, setCanal] = useState<ChannelPublic | null>(null);
  const [segments, setSegments] = useState<WheelSegment[]>([]);
  const [estado, setEstado] = useState<"cargando" | "form" | "ruleta" | "error">("cargando");
  const [errCarga, setErrCarga] = useState("");

  // Datos del participante
  const [factura, setFactura] = useState("");
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [error, setError] = useState("");

  const [spinning, setSpinning] = useState(false);
  const [target, setTarget] = useState<number | null>(null);
  const [result, setResult] = useState<SpinResult | null>(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    (async () => {
      if (!slug) return;
      try {
        const [info, cfg] = await Promise.all([api.infoCanal(slug), api.ruletaCanal(slug)]);
        setCanal(info);
        setSegments(cfg);
        setEstado("form");
      } catch (e) {
        setErrCarga(e instanceof Error ? e.message : "No disponible.");
        setEstado("error");
      }
    })();
  }, [slug]);

  function continuar(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (canal?.modo === "factura" && !factura.trim()) {
      setError("Ingresa el número de factura.");
      return;
    }
    if (canal?.modo === "vendedor" && (!nombre.trim() || !telefono.trim())) {
      setError("Ingresa nombre y teléfono.");
      return;
    }
    setEstado("ruleta");
  }

  async function girar() {
    if (spinning) return;
    setError("");
    setSpinning(true);
    try {
      const body =
        canal?.modo === "factura"
          ? { factura: factura.trim() }
          : { nombre: nombre.trim(), telefono: telefono.trim() };
      const res = await api.girarCanal(slug, body);
      setResult(res);
      setTarget(res.segment_index);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo girar.");
      setSpinning(false);
    }
  }

  const onDone = useCallback(() => setShowResult(true), []);

  return (
    <main className="min-h-screen bg-stadium">
      <div className="mx-auto flex min-h-screen max-w-md flex-col items-center px-5 py-8">
        <div className="mb-4">
          <Logo dark />
        </div>

        {estado === "cargando" && <p className="mt-10 text-white/70">Cargando…</p>}

        {estado === "error" && (
          <Card className="mt-8 w-full text-center">
            <div className="text-5xl">🚫</div>
            <p className="mt-2 font-bold text-navy">Punto de giro no disponible</p>
            <p className="text-sm text-navy/60">{errCarga}</p>
          </Card>
        )}

        {estado === "form" && canal && (
          <div className="mt-4 w-full">
            <div className="mb-4 text-center">
              <span className="inline-flex rounded-full bg-brand-yellow/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-brand-yellow">
                {canal.tipo === "sede" ? "🏬 Sede" : "🧑‍💼 Vendedor"} · {canal.nombre}
              </span>
            </div>
            <Card>
              <h1 className="text-2xl font-extrabold text-navy">¡Gira y gana! 🎡</h1>
              <p className="mt-1 text-sm text-navy/60">
                {canal.modo === "factura"
                  ? "Ingresa el número de tu factura para participar."
                  : "Déjanos tus datos y gira la ruleta."}
              </p>
              <form onSubmit={continuar} className="mt-5 space-y-4">
                {canal.modo === "factura" ? (
                  <Input
                    label="Número de factura"
                    value={factura}
                    onChange={(e) => setFactura(e.target.value)}
                    placeholder="Ej. F-00123"
                    autoFocus
                  />
                ) : (
                  <>
                    <Input label="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Tu nombre" />
                    <Input label="Teléfono / WhatsApp" value={telefono} onChange={(e) => setTelefono(e.target.value)} placeholder="300 000 0000" inputMode="tel" />
                  </>
                )}
                {error && <p className="text-sm font-medium text-brand-red">{error}</p>}
                <Button type="submit" variant="yellow" className="w-full py-4 text-base">
                  Continuar a la ruleta →
                </Button>
              </form>
            </Card>
          </div>
        )}

        {estado === "ruleta" && canal && (
          <div className="w-full text-center">
            <h1 className="text-2xl font-extrabold text-white">
              ¡Gira, <span className="text-flame">{nombre.split(" ")[0] || "y gana"}</span>! 🏆
            </h1>
            <p className="mt-1 text-sm text-white/60">{canal.nombre}</p>
            <div className="my-6">
              <Wheel segments={segments} spinning={spinning} targetIndex={target} onDone={onDone} />
            </div>
            {error && <p className="mb-3 text-sm font-medium text-brand-red">{error}</p>}
            <button
              onClick={girar}
              disabled={spinning}
              className="btn-pulse mx-auto flex items-center gap-2 rounded-2xl bg-gradient-to-b from-brand-yellow to-[#E6A700] px-12 py-5 text-xl font-extrabold text-navy shadow-glow transition hover:scale-105 disabled:animate-none disabled:opacity-60"
            >
              {spinning ? "Girando…" : "🎯 ¡GIRAR!"}
            </button>
          </div>
        )}
      </div>

      <Confetti active={showResult && !!result?.gano} />

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
              transition={{ type: "spring", stiffness: 260, damping: 18 }}
              className="w-full max-w-sm rounded-3xl bg-white p-8 text-center shadow-card"
            >
              <div className="text-7xl">{result.gano ? "🎉" : "🙌"}</div>
              <h2 className="mt-3 text-3xl font-extrabold text-navy">
                {result.gano ? "¡GANASTE!" : "¡Gracias por participar!"}
              </h2>
              {result.gano && result.prize_nombre && (
                <div className="my-4 rounded-2xl bg-gradient-to-br from-navy to-navy-light p-5 text-2xl font-extrabold text-brand-yellow shadow-glow">
                  {result.prize_nombre}
                </div>
              )}
              <p className="text-sm text-navy/70">{result.mensaje}</p>
              {result.gano && (
                <p className="mt-4 rounded-xl bg-brand-green/10 px-4 py-2 text-sm font-bold text-brand-green">
                  🎁 Reclama tu premio en el momento
                </p>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
