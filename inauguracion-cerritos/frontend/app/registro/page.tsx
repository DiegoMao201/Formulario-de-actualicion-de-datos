"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button, Card, Input, Logo } from "@/components/ui";

function RegistroForm() {
  const router = useRouter();
  const params = useSearchParams();
  const refParam = params.get("ref") || "";

  const [form, setForm] = useState({
    nombre: "",
    telefono: "",
    correo: "",
    cedula: "",
    direccion: "",
  });
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!consent) {
      setError("Debes aceptar el tratamiento de datos personales.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.registrar({
        ...form,
        consentimiento_datos: true,
        referral_code: refParam || undefined,
      });
      // Guardamos los datos del éxito para la siguiente pantalla
      sessionStorage.setItem("lead", JSON.stringify(res));
      router.push("/exito");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stadium py-8">
      <div className="mx-auto max-w-md px-5">
        <div className="mb-6 flex justify-center">
          <Logo dark />
        </div>

        <Card>
          <h1 className="text-2xl font-extrabold text-navy">Regístrate y participa 🎁</h1>
          <p className="mt-1 text-sm text-navy/60">
            Completa tus datos para recibir tu cupón del 10% y girar la ruleta.
          </p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <Input label="Nombre completo" required value={form.nombre} onChange={set("nombre")} placeholder="Tu nombre" />
            <Input label="Teléfono / WhatsApp" required value={form.telefono} onChange={set("telefono")} placeholder="300 000 0000" inputMode="tel" />
            <Input label="Correo electrónico" type="email" required value={form.correo} onChange={set("correo")} placeholder="tucorreo@email.com" />
            <Input label="Cédula" required value={form.cedula} onChange={set("cedula")} placeholder="Número de documento" inputMode="numeric" />
            <Input label="Dirección (opcional)" value={form.direccion} onChange={set("direccion")} placeholder="Tu dirección" />

            <label className="flex items-start gap-3 rounded-xl bg-navy/5 p-3 text-sm text-navy/80">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 h-5 w-5 accent-navy"
              />
              <span>
                Autorizo el tratamiento de mis datos personales conforme a la{" "}
                <strong>Ley 1581 de 2012 (Habeas Data)</strong> y la política de privacidad de
                Ferreinox S.A.S. BIC para fines comerciales de esta campaña.
              </span>
            </label>

            {error && (
              <p className="rounded-lg bg-brand-red/10 px-3 py-2 text-sm font-medium text-brand-red">
                {error}
              </p>
            )}

            <Button type="submit" variant="yellow" className="w-full py-4 text-base" disabled={loading}>
              {loading ? "Registrando…" : "Recibir mi cupón →"}
            </Button>
          </form>
        </Card>

        <p className="mt-4 text-center text-xs text-white/40">
          Tus datos están protegidos. Ferreinox S.A.S. BIC
        </p>
      </div>
    </main>
  );
}

export default function RegistroPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-stadium" />}>
      <RegistroForm />
    </Suspense>
  );
}
