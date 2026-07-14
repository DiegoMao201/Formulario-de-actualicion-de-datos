// Cliente de la API. En producción, /api se enruta al backend (mismo dominio vía Traefik).
// En local, NEXT_PUBLIC_API_URL=http://localhost:8000

const BASE = process.env.NEXT_PUBLIC_API_URL || "";

export type WheelSegment = {
  id: string;
  nombre: string;
  color: string;
  es_perdedor: boolean;
};

export type LeadResponse = {
  id: string;
  nombre: string;
  coupon_code: string;
  referral_code: string;
  magic_token: string;
  whatsapp_url: string;
};

export type SpinResult = {
  gano: boolean;
  prize_id: string | null;
  prize_nombre: string | null;
  segment_index: number;
  mensaje: string;
};

export type Prize = {
  id: string;
  nombre: string;
  descripcion?: string | null;
  stock_total: number;
  stock_restante: number;
  probabilidad: number;
  color: string;
  es_perdedor: boolean;
  activo: boolean;
  orden: number;
};

export type Metrics = {
  total_participantes: number;
  total_giros: number;
  premios_ganados: number;
  premios_entregados: number;
  premios_disponibles: number;
  tasa_conversion: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = "Error inesperado";
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

function auth(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

// ---------- Público ----------
export const api = {
  registrar: (data: Record<string, unknown>) =>
    req<LeadResponse>("/api/leads", { method: "POST", body: JSON.stringify(data) }),

  ruletaConfig: () => req<WheelSegment[]>("/api/ruleta/config"),

  validarMagic: (token: string) =>
    req<{ valido: boolean; usado: boolean; nombre: string | null }>(`/api/magic/${token}`),

  girar: (token: string) =>
    req<SpinResult>(`/api/ruleta/spin/${token}`, { method: "POST" }),

  // ---------- Admin ----------
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  metrics: (token: string) =>
    req<Metrics>("/api/admin/metrics", { headers: auth(token) }),

  premios: (token: string) =>
    req<Prize[]>("/api/admin/prizes", { headers: auth(token) }),

  crearPremio: (token: string, data: Record<string, unknown>) =>
    req<Prize>("/api/admin/prizes", {
      method: "POST",
      headers: auth(token),
      body: JSON.stringify(data),
    }),

  actualizarPremio: (token: string, id: string, data: Record<string, unknown>) =>
    req<Prize>(`/api/admin/prizes/${id}`, {
      method: "PUT",
      headers: auth(token),
      body: JSON.stringify(data),
    }),

  eliminarPremio: (token: string, id: string) =>
    req<void>(`/api/admin/prizes/${id}`, { method: "DELETE", headers: auth(token) }),

  redimir: (token: string, qrToken: string) =>
    req<{
      valido: boolean;
      ya_redimido: boolean;
      mensaje: string;
      premio?: string | null;
      cliente?: string | null;
      fecha_giro?: string | null;
    }>("/api/admin/redeem", {
      method: "POST",
      headers: auth(token),
      body: JSON.stringify({ token: qrToken }),
    }),

  leadsCsvUrl: () => `${BASE}/api/admin/leads.csv`,
};
