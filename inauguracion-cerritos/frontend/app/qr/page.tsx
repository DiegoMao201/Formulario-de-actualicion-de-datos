"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button, Card, Logo } from "@/components/ui";

export default function QrPage() {
  const src = api.qrRegistroUrl();
  const [descargando, setDescargando] = useState(false);

  async function descargar() {
    setDescargando(true);
    try {
      const res = await fetch(src);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "QR-Tienda-Pintuco-Cerritos.png";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDescargando(false);
    }
  }

  const compartir = () => {
    const texto =
      "🎨🎡 ¡Participa en la inauguración de la Tienda Pintuco Cerritos! Escanea el QR o entra aquí y gana premios: https://cerritos.ferreinox.co/registro";
    return `https://wa.me/?text=${encodeURIComponent(texto)}`;
  };

  return (
    <main className="min-h-screen bg-stadium py-8">
      <div className="mx-auto max-w-md px-5">
        <div className="mb-6 flex justify-center">
          <Logo dark />
        </div>

        <Card className="text-center">
          <h1 className="text-2xl font-extrabold text-navy">Comparte y suma participantes 🚀</h1>
          <p className="mt-1 text-sm text-navy/60">
            Muestra este código para que la gente lo escanee, o compártelo por WhatsApp.
          </p>

          <div className="my-6 flex justify-center">
            <div className="rounded-3xl bg-white p-4 shadow-card ring-4 ring-brand-yellow">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="QR de registro" width={260} height={260} className="h-64 w-64" />
            </div>
          </div>

          <p className="mb-5 text-sm font-semibold text-navy">
            Lleva a: <span className="text-navy/60">cerritos.ferreinox.co/registro</span>
          </p>

          <div className="space-y-2">
            <a href={compartir()} target="_blank" rel="noopener noreferrer">
              <Button className="w-full bg-brand-green text-white hover:brightness-95">
                📲 Compartir por WhatsApp
              </Button>
            </a>
            <Button variant="outline" className="w-full" onClick={descargar} disabled={descargando}>
              {descargando ? "Descargando…" : "⬇ Descargar QR (PNG)"}
            </Button>
          </div>
        </Card>

        <p className="mt-4 text-center text-xs text-white/50">
          Para colaboradores · Tienda Pintuco Cerritos
        </p>
      </div>
    </main>
  );
}
