"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Channel } from "@/lib/api";
import { useRequireAuth } from "@/lib/auth";
import { Button, Card, Input } from "@/components/ui";
import AdminShell from "@/components/AdminShell";

const NUEVO = { tipo: "sede", nombre: "", modo: "factura", activo: true, orden: 0 };

export default function CanalesPage() {
  const { token, ready } = useRequireAuth();
  const [canales, setCanales] = useState<Channel[]>([]);
  const [form, setForm] = useState<Record<string, unknown>>(NUEVO);
  const [editId, setEditId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [qrCanal, setQrCanal] = useState<Channel | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setCanales(await api.canales(token));
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
      // El modo se deriva del tipo: sede->factura, vendedor->vendedor
      const modo = form.tipo === "sede" ? "factura" : "vendedor";
      const payload = { ...form, modo };
      if (editId) await api.actualizarCanal(token, editId, payload);
      else await api.crearCanal(token, payload);
      setForm(NUEVO);
      setEditId(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function eliminar(id: string) {
    if (!token || !confirm("¿Eliminar este canal y sus premios? (el historial de giros se conserva)")) return;
    await api.eliminarCanal(token, id);
    load();
  }

  function editar(c: Channel) {
    setEditId(c.id);
    setForm({ tipo: c.tipo, nombre: c.nombre, modo: c.modo, activo: c.activo, orden: c.orden });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const sedes = canales.filter((c) => c.tipo === "sede");
  const vendedores = canales.filter((c) => c.tipo === "vendedor");

  if (!ready) return null;

  return (
    <AdminShell>
      <h1 className="mb-4 text-xl font-extrabold text-navy">Sedes y Vendedores</h1>

      <Card className="mb-6">
        <h2 className="mb-3 font-bold text-navy">{editId ? "Editar canal" : "Nuevo canal"}</h2>
        <form onSubmit={guardar} className="grid gap-3 md:grid-cols-2">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-navy">Tipo</span>
            <select
              value={form.tipo as string}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              className="w-full rounded-xl border border-navy/15 bg-white px-4 py-3 text-navy"
            >
              <option value="sede">🏬 Sede (giro con factura)</option>
              <option value="vendedor">🧑‍💼 Vendedor (nombre + teléfono)</option>
            </select>
          </label>
          <Input label="Nombre" required value={form.nombre as string} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          <Input label="Orden" type="number" value={form.orden as number} onChange={(e) => setForm({ ...form, orden: Number(e.target.value) })} />
          <label className="flex items-center gap-2 pt-7 text-sm text-navy">
            <input type="checkbox" checked={form.activo as boolean} onChange={(e) => setForm({ ...form, activo: e.target.checked })} className="h-5 w-5 accent-navy" />
            Activo
          </label>
          <div className="flex gap-2 md:col-span-2">
            <Button type="submit" className="flex-1">{editId ? "Guardar" : "Crear canal"}</Button>
            {editId && (
              <Button type="button" variant="outline" onClick={() => { setEditId(null); setForm(NUEVO); }}>Cancelar</Button>
            )}
          </div>
        </form>
        {error && <p className="mt-3 text-sm text-brand-red">{error}</p>}
      </Card>

      {[{ t: "🏬 Sedes", list: sedes }, { t: "🧑‍💼 Vendedores", list: vendedores }].map((grp) => (
        <div key={grp.t} className="mb-6">
          <h3 className="mb-2 text-sm font-bold text-navy/70">{grp.t} ({grp.list.length})</h3>
          <div className="space-y-2">
            {grp.list.map((c) => (
              <Card key={c.id} className="flex flex-wrap items-center gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-navy">{c.nombre}</span>
                    {!c.activo && <span className="rounded bg-brand-red/10 px-1.5 text-[10px] text-brand-red">INACTIVO</span>}
                  </div>
                  <div className="text-xs text-navy/50">/girar/{c.slug} · modo {c.modo}</div>
                </div>
                <button onClick={() => setQrCanal(c)} className="text-sm font-medium text-navy hover:underline">QR</button>
                <Link href={`/admin/premios?channel=${c.id}`} className="text-sm font-medium text-navy hover:underline">Premios</Link>
                <button onClick={() => editar(c)} className="text-sm font-medium text-navy hover:underline">Editar</button>
                <button onClick={() => eliminar(c.id)} className="text-sm font-medium text-brand-red hover:underline">Eliminar</button>
              </Card>
            ))}
          </div>
        </div>
      ))}

      {/* Modal QR del canal */}
      {qrCanal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-6" onClick={() => setQrCanal(null)}>
          <Card className="w-full max-w-xs text-center" >
            <p className="font-bold text-navy">{qrCanal.nombre}</p>
            <p className="mb-3 text-xs text-navy/50">Escanea para girar la ruleta de este punto</p>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={api.qrCanalUrl(qrCanal.slug)} alt={`QR ${qrCanal.nombre}`} className="mx-auto h-56 w-56 rounded-xl ring-4 ring-brand-yellow" />
            <a
              href={api.qrCanalUrl(qrCanal.slug)}
              download={`QR-${qrCanal.slug}.png`}
              className="mt-4 block rounded-xl bg-navy py-2.5 text-sm font-semibold text-white"
            >
              ⬇ Descargar QR
            </a>
            <button onClick={() => setQrCanal(null)} className="mt-2 text-xs text-navy/50">Cerrar</button>
          </Card>
        </div>
      )}
    </AdminShell>
  );
}
