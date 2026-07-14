"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { Button, Card, Logo } from "@/components/ui";

type Estado = {
  encontrado: boolean;
  tipo: "premio" | "cupon" | null;
  titulo: string | null;
  cliente: string | null;
  redimido: boolean;
  fecha_redencion: string | null;
};

function ValidarInner() {
  const params = useSearchParams();
  const t = params.get("t") || "";
  const [estado, setEstado] = useState<Estado | null>(null);
  const [cargando, setCargando] = useState(true);
  const [esAdmin, setEsAdmin] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [mensajeCanje, setMensajeCanje] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    if (!t) {
      setError("QR sin token.");
      setCargando(false);
      return;
    }
    try {
      setEstado(await api.validar(t));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setCargando(false);
    }
  }, [t]);

  useEffect(() => {
    setEsAdmin(!!getToken());
    cargar();
  }, [cargar]);

  async function canjear() {
    const token = getToken();
    if (!token) return;
    setProcesando(true);
    setMensajeCanje("");
    try {
      const r = await api.redimir(token, t);
      setMensajeCanje(r.mensaje);
      await cargar();
    } catch (e) {
      setMensajeCanje(e instanceof Error ? e.message : "Error");
    } finally {
      setProcesando(false);
    }
  }

  const color = !estado?.encontrado
    ? "ring-brand-red"
    : estado.redimido
    ? "ring-brand-yellow"
    : "ring-brand-green";

  return (
    <main className="min-h-screen bg-stadium py-8">
      <div className="mx-auto max-w-md px-5">
        <div className="mb-6 flex justify-center">
          <Logo dark />
        </div>

        {cargando ? (
          <Card className="text-center text-navy/60">Validando…</Card>
        ) : !estado?.encontrado ? (
          <Card className="text-center ring-2 ring-brand-red">
            <div className="text-5xl">❌</div>
            <p className="mt-2 text-lg font-bold text-navy">QR no válido</p>
            <p className="text-sm text-navy/60">{error || "Este código no existe en el sistema."}</p>
          </Card>
        ) : (
          <Card className={`text-center ring-2 ${color}`}>
            <div className="text-5xl">{estado.redimido ? "⛔" : estado.tipo === "premio" ? "🏆" : "🎁"}</div>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-navy/50">
              {estado.tipo === "premio" ? "Premio" : "Cupón de descuento"}
            </p>
            <div className="my-3 rounded-2xl bg-navy p-4 text-xl font-extrabold text-brand-yellow">
              {estado.titulo}
            </div>
            {estado.cliente && <p className="text-sm text-navy/70">Cliente: <strong>{estado.cliente}</strong></p>}

            <div
              className={`mt-4 rounded-xl px-4 py-3 text-sm font-bold ${
                estado.redimido ? "bg-brand-red/10 text-brand-red" : "bg-brand-green/10 text-brand-green"
              }`}
            >
              {estado.redimido ? "⛔ YA FUE RECLAMADO" : "✅ VÁLIDO — sin reclamar"}
            </div>

            {mensajeCanje && <p className="mt-3 text-sm font-semibold text-navy">{mensajeCanje}</p>}

            {/* Acción de canje: solo visible con sesión admin */}
            {esAdmin ? (
              !estado.redimido && (
                <Button className="mt-5 w-full" onClick={canjear} disabled={procesando}>
                  {procesando ? "Procesando…" : "✅ Marcar como entregado / usado"}
                </Button>
              )
            ) : (
              <p className="mt-5 text-xs text-navy/50">
                Muestra esta pantalla en la tienda para reclamar. El personal lo validará.
              </p>
            )}

            {esAdmin && (
              <Link href="/admin/escanear" className="mt-4 block text-xs font-medium text-navy/60 hover:underline">
                ← Volver al escáner
              </Link>
            )}
          </Card>
        )}
      </div>
    </main>
  );
}

export default function ValidarPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-stadium" />}>
      <ValidarInner />
    </Suspense>
  );
}
