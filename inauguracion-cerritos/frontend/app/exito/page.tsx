"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { LeadResponse } from "@/lib/api";
import { Button, Card, Logo } from "@/components/ui";

export default function ExitoPage() {
  const [lead, setLead] = useState<LeadResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("lead");
    if (raw) setLead(JSON.parse(raw));
  }, []);

  const refLink =
    lead && typeof window !== "undefined"
      ? `${window.location.origin}/registro?ref=${lead.referral_code}`
      : "";

  if (!lead) {
    return (
      <main className="grid min-h-screen place-items-center bg-stadium px-6 text-center text-white">
        <div>
          <p className="mb-4 text-white/70">No encontramos tu registro.</p>
          <Link href="/registro" className="font-semibold text-brand-yellow">
            Volver a registrarme →
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-stadium py-8">
      <div className="mx-auto max-w-md px-5">
        <div className="mb-6 flex justify-center">
          <Logo dark />
        </div>

        <Card className="text-center">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-brand-yellow text-3xl">
            🎉
          </div>
          <h1 className="text-2xl font-extrabold text-navy">
            ¡Listo, {lead.nombre.split(" ")[0]}!
          </h1>
          <p className="mt-1 text-sm text-navy/60">
            Te enviamos tu cupón al correo. Este es tu código:
          </p>

          <div className="my-5 rounded-2xl bg-navy p-5">
            <div className="text-xs uppercase tracking-widest text-white/50">Cupón 10% OFF</div>
            <div className="mt-1 text-2xl font-extrabold text-brand-yellow">{lead.coupon_code}</div>
          </div>

          <div className="rounded-2xl bg-brand-green/10 p-5">
            <p className="text-sm font-semibold text-navy">🎡 ¡Ahora gira la ruleta!</p>
            <p className="mt-1 text-xs text-navy/60">
              Envíate tu enlace exclusivo por WhatsApp para participar (un solo uso).
            </p>
            <a href={lead.whatsapp_url} target="_blank" rel="noopener noreferrer">
              <Button variant="yellow" className="mt-3 w-full bg-brand-green text-white hover:brightness-95">
                <span>📲</span> Enviarme el enlace por WhatsApp
              </Button>
            </a>
            <Link href={`/ruleta?token=${lead.magic_token}`}>
              <Button variant="outline" className="mt-2 w-full">
                O girar aquí mismo →
              </Button>
            </Link>
          </div>

          <div className="mt-5 border-t border-navy/10 pt-4">
            <p className="text-xs font-semibold text-navy/70">Invita amigos y gana un giro extra 🎯</p>
            <button
              onClick={() => {
                navigator.clipboard.writeText(refLink);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              className="mt-2 w-full truncate rounded-lg bg-navy/5 px-3 py-2 text-xs text-navy/70 transition hover:bg-navy/10"
            >
              {copied ? "✅ ¡Enlace copiado!" : refLink}
            </button>
          </div>
        </Card>
      </div>
    </main>
  );
}
