"use client";
import { useCallback, useEffect, useState } from "react";
import { api, Prize } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import { Button, Card, Input } from "@/components/ui";
import AdminShell from "@/components/AdminShell";

const VACIO = {
  nombre: "",
  descripcion: "",
  stock_total: 0,
  probabilidad: 0,
  color: "#0A2E57",
  es_perdedor: false,
  activo: true,
  orden: 0,
};

export default function PremiosPage() {
  const { token, ready } = useRequireAuth();
  const [premios, setPremios] = useState<Prize[]>([]);
  const [form, setForm] = useState<Record<string, unknown>>(VACIO);
  const [editId, setEditId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setPremios(await api.premios(token));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }, [token]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError("");
    try {
      if (editId) await api.actualizarPremio(token, editId, form);
      else await api.crearPremio(token, form);
      setForm(VACIO);
      setEditId(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function eliminar(id: string) {
    if (!token || !confirm("¿Eliminar este premio?")) return;
    await api.eliminarPremio(token, id);
    load();
  }

  function editar(p: Prize) {
    setEditId(p.id);
    setForm({
      nombre: p.nombre,
      descripcion: p.descripcion || "",
      stock_total: p.stock_total,
      probabilidad: p.probabilidad,
      color: p.color,
      es_perdedor: p.es_perdedor,
      activo: p.activo,
      orden: p.orden,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const num = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: Number(e.target.value) });
  const str = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const totalProb = premios.reduce((a, p) => a + (p.activo ? p.probabilidad : 0), 0);

  if (!ready) return null;

  return (
    <AdminShell>
      <h1 className="mb-4 text-xl font-extrabold text-navy">Gestión de premios</h1>

      <Card className="mb-6">
        <h2 className="mb-3 font-bold text-navy">{editId ? "Editar premio" : "Nuevo premio"}</h2>
        <form onSubmit={guardar} className="grid gap-3 md:grid-cols-2">
          <Input label="Nombre" required value={form.nombre as string} onChange={str("nombre")} />
          <Input label="Descripción" value={form.descripcion as string} onChange={str("descripcion")} />
          <Input label="Stock total" type="number" min={0} value={form.stock_total as number} onChange={num("stock_total")} />
          <Input label="Probabilidad (peso 0-1)" type="number" step="0.01" min={0} value={form.probabilidad as number} onChange={num("probabilidad")} />
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-navy">Color</span>
            <input type="color" value={form.color as string} onChange={str("color")} className="h-11 w-full rounded-xl border border-navy/15" />
          </label>
          <Input label="Orden" type="number" value={form.orden as number} onChange={num("orden")} />
          <label className="flex items-center gap-2 text-sm text-navy">
            <input type="checkbox" checked={form.es_perdedor as boolean} onChange={(e) => setForm({ ...form, es_perdedor: e.target.checked })} className="h-5 w-5 accent-navy" />
            Es &quot;Sigue participando&quot; (sin stock)
          </label>
          <label className="flex items-center gap-2 text-sm text-navy">
            <input type="checkbox" checked={form.activo as boolean} onChange={(e) => setForm({ ...form, activo: e.target.checked })} className="h-5 w-5 accent-navy" />
            Activo (visible en la ruleta)
          </label>
          <div className="flex gap-2 md:col-span-2">
            <Button type="submit" className="flex-1">{editId ? "Guardar cambios" : "Crear premio"}</Button>
            {editId && (
              <Button type="button" variant="outline" onClick={() => { setEditId(null); setForm(VACIO); }}>
                Cancelar
              </Button>
            )}
          </div>
        </form>
        {error && <p className="mt-3 text-sm text-brand-red">{error}</p>}
      </Card>

      <div className="mb-3 flex items-center justify-between text-sm">
        <span className="text-navy/60">{premios.length} premios</span>
        <span className={totalProb > 0 ? "text-navy/60" : "text-brand-red"}>
          Suma de pesos activos: <strong>{totalProb.toFixed(2)}</strong>
        </span>
      </div>

      <div className="space-y-2">
        {premios.map((p) => (
          <Card key={p.id} className="flex items-center gap-4 py-3">
            <span className="h-8 w-8 shrink-0 rounded-lg" style={{ background: p.color }} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate font-semibold text-navy">{p.nombre}</span>
                {p.es_perdedor && <span className="rounded bg-navy/10 px-1.5 text-[10px] text-navy/60">SIN PREMIO</span>}
                {!p.activo && <span className="rounded bg-brand-red/10 px-1.5 text-[10px] text-brand-red">OCULTO</span>}
              </div>
              <div className="text-xs text-navy/50">
                Peso {p.probabilidad} · Stock {p.stock_restante}/{p.stock_total}
              </div>
            </div>
            <button onClick={() => editar(p)} className="text-sm font-medium text-navy hover:underline">Editar</button>
            <button onClick={() => eliminar(p.id)} className="text-sm font-medium text-brand-red hover:underline">Eliminar</button>
          </Card>
        ))}
      </div>
    </AdminShell>
  );
}
