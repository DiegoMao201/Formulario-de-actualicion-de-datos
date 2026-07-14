"use client";
import { useEffect, useState } from "react";
import { api, Metrics } from "@/lib/api";
import { getToken, saveToken } from "@/lib/auth";
import { Button, Card, Input } from "@/components/ui";
import AdminShell from "@/components/AdminShell";

function Login({ onOk }: { onOk: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(email, password);
      saveToken(res.access_token);
      onOk();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-stadium px-5">
      <Card className="w-full max-w-sm">
        <h1 className="text-2xl font-extrabold text-navy">Panel administrativo</h1>
        <p className="mt-1 text-sm text-navy/60">Tienda Pintuco Cerritos</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <Input label="Correo" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input label="Contraseña" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm font-medium text-brand-red">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Ingresando…" : "Ingresar"}
          </Button>
        </form>
      </Card>
    </main>
  );
}

function Stat({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <Card className="text-center">
      <div className={`text-3xl font-extrabold ${accent || "text-navy"}`}>{value}</div>
      <div className="mt-1 text-xs font-medium uppercase tracking-wide text-navy/50">{label}</div>
    </Card>
  );
}

function Dashboard() {
  const [m, setM] = useState<Metrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      const t = getToken();
      if (!t) return;
      try {
        setM(await api.metrics(t));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error");
      }
    };
    load();
    const id = setInterval(load, 8000); // tiempo real (poll cada 8s)
    return () => clearInterval(id);
  }, []);

  return (
    <AdminShell>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-extrabold text-navy">Dashboard en vivo</h1>
        <a href={api.leadsCsvUrl()} className="text-sm font-semibold text-navy hover:underline">
          ⬇ Exportar leads CSV
        </a>
      </div>
      {error && <p className="mb-4 text-sm text-brand-red">{error}</p>}
      {!m ? (
        <p className="text-navy/50">Cargando métricas…</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <Stat label="Participantes" value={m.total_participantes} />
          <Stat label="Giros" value={m.total_giros} accent="text-brand-green" />
          <Stat label="Conversión %" value={`${m.tasa_conversion}%`} />
          <Stat label="Premios ganados" value={m.premios_ganados} accent="text-brand-red" />
          <Stat label="Premios entregados" value={m.premios_entregados} />
          <Stat label="Disponibles" value={m.premios_disponibles} accent="text-navy-light" />
        </div>
      )}
    </AdminShell>
  );
}

export default function AdminPage() {
  const [logged, setLogged] = useState<boolean | null>(null);
  useEffect(() => setLogged(!!getToken()), []);
  if (logged === null) return null;
  return logged ? <Dashboard /> : <Login onOk={() => setLogged(true)} />;
}
