"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import { Button, Card } from "@/components/ui";
import AdminShell from "@/components/AdminShell";

type Resultado = {
  valido: boolean;
  ya_redimido: boolean;
  mensaje: string;
  premio?: string | null;
  cliente?: string | null;
};

const REGION_ID = "qr-reader";

export default function EscanearPage() {
  const { token, ready } = useRequireAuth();
  const scannerRef = useRef<any>(null);
  const [scanning, setScanning] = useState(false);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [error, setError] = useState("");
  const procesando = useRef(false);

  const detener = useCallback(async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
        await scannerRef.current.clear();
      } catch {}
      scannerRef.current = null;
    }
    setScanning(false);
  }, []);

  const onScan = useCallback(
    async (texto: string) => {
      if (procesando.current || !token) return;
      procesando.current = true;
      await detener();
      try {
        const r = await api.redimir(token, texto);
        setResultado(r);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error al validar.");
      } finally {
        procesando.current = false;
      }
    },
    [token, detener]
  );

  const iniciar = useCallback(async () => {
    setError("");
    setResultado(null);
    procesando.current = false;
    try {
      const { Html5Qrcode } = await import("html5-qrcode");
      const scanner = new Html5Qrcode(REGION_ID);
      scannerRef.current = scanner;
      setScanning(true);
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 240, height: 240 } },
        (decoded: string) => onScan(decoded),
        () => {}
      );
    } catch (e) {
      setError("No se pudo acceder a la cámara. Revisa los permisos.");
      setScanning(false);
    }
  }, [onScan]);

  useEffect(() => {
    return () => {
      detener();
    };
  }, [detener]);

  if (!ready) return null;

  return (
    <AdminShell>
      <h1 className="mb-4 text-xl font-extrabold text-navy">Escanear QR de premio</h1>

      <Card>
        <div id={REGION_ID} className="mx-auto w-full max-w-sm overflow-hidden rounded-2xl bg-navy-dark" />
        {!scanning && !resultado && (
          <Button className="mt-4 w-full" onClick={iniciar}>📷 Iniciar cámara</Button>
        )}
        {scanning && (
          <Button variant="outline" className="mt-4 w-full" onClick={detener}>Detener</Button>
        )}
        {error && <p className="mt-3 text-center text-sm text-brand-red">{error}</p>}
      </Card>

      {resultado && (
        <Card
          className={`mt-5 text-center ${
            !resultado.valido
              ? "ring-2 ring-brand-red"
              : resultado.ya_redimido
              ? "ring-2 ring-brand-yellow"
              : "ring-2 ring-brand-green"
          }`}
        >
          <div className="text-5xl">
            {!resultado.valido ? "❌" : resultado.ya_redimido ? "⚠️" : "✅"}
          </div>
          <p className="mt-2 text-lg font-bold text-navy">{resultado.mensaje}</p>
          {resultado.premio && (
            <div className="my-3 rounded-xl bg-navy p-3 text-lg font-extrabold text-brand-yellow">
              {resultado.premio}
            </div>
          )}
          {resultado.cliente && (
            <p className="text-sm text-navy/60">Cliente: {resultado.cliente}</p>
          )}
          <Button className="mt-5 w-full" onClick={iniciar}>Escanear otro</Button>
        </Card>
      )}
    </AdminShell>
  );
}
