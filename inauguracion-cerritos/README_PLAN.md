# 🎡 Plataforma de Inauguración — Tienda Ferreinox Cerritos

Plataforma de captación de leads + ruleta de premios + panel de administración para la
inauguración de la tienda física de **Cerritos (Pereira)**.

> **Independencia total:** vive en la subcarpeta `inauguracion-cerritos/` de este repo, se
> despliega como un **recurso Coolify separado** con su propia base de datos y su propio
> **subdominio**. **No comparte nada** con el Portal de Vinculación (Streamlit) que ya
> circula entre los clientes. Nada nuevo se agrega en la raíz del repo.

---

## 1. Arquitectura general

```
                          Internet (QR físico en tienda)
                                     │
                        cerritos.tudominio.com  (Traefik / Coolify)
                                     │
                 ┌───────────────────┴────────────────────┐
                 │                                         │
        Next.js (frontend)                        FastAPI (backend/API)
        - /registro  (formulario)                 - /api/*  endpoints
        - /exito     (cupón + wa.me)               - lógica segura de ruleta
        - /ruleta    (Framer Motion)              - firma/verificación JWT de QRs
        - /admin/*   (dashboard, escáner)          - envío SendGrid
                 │                                         │
                 └──────────────── llama a ───────────────┘
                                     │
                          PostgreSQL (contenedor dedicado)
                                     │
                          SendGrid (emails transaccionales)
```

**Regla de oro:** el resultado de la ruleta y toda validación de premios se decide **en el
backend**. El cliente nunca conoce las probabilidades ni puede forzar un premio.

### Despliegue en Coolify (3 recursos independientes)
1. **PostgreSQL** — base de datos gestionada por Coolify (backups automáticos).
2. **backend** — imagen Docker de FastAPI (Base Directory: `inauguracion-cerritos/backend`).
3. **frontend** — imagen Docker de Next.js (Base Directory: `inauguracion-cerritos/frontend`).

Ruteo por subdominio con Traefik:
- `cerritos.tudominio.com`        → frontend (Next.js)
- `cerritos.tudominio.com/api`    → backend (FastAPI)  *(o `api-cerritos.tudominio.com`)*

---

## 2. Modelo de base de datos (PostgreSQL + SQLAlchemy + Alembic)

### `leads` — participantes registrados
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| nombre | str | |
| telefono | str | indexado |
| correo | str | indexado |
| cedula | str | único (anti-duplicados) |
| direccion | str | |
| consentimiento_datos | bool | **Ley 1581 Habeas Data** (obligatorio) |
| consentimiento_ts | datetime | sello de tiempo del consentimiento |
| coupon_code | str | cupón 10% (único) |
| coupon_jwt | text | QR del cupón firmado |
| referral_code | str | código propio para invitar |
| referred_by | UUID FK→leads | quién lo invitó (nullable) |
| created_at | datetime | |

### `prizes` — inventario de premios (editable en admin)
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| nombre | str | |
| descripcion | str | |
| stock_total | int | inventario inicial |
| stock_restante | int | decrece al ganar |
| probabilidad | float | peso relativo (0–1) |
| activo | bool | |
| color | str | color del segmento en la ruleta |

### `spins` — cada giro de la ruleta
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| lead_id | UUID FK→leads | |
| prize_id | UUID FK→prizes | nullable (si "sigue participando") |
| server_seed | str | semilla firmada — **provably fair** |
| resultado_ts | datetime | |
| prize_jwt | text | QR del premio firmado (JWT) |
| redeemed | bool | ¿ya se entregó en tienda? |
| redeemed_at | datetime | |
| redeemed_by | str | admin que lo entregó |

### `magic_links` — enlaces de un solo uso hacia /ruleta
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| lead_id | UUID FK→leads | |
| token | str | único, aleatorio |
| used | bool | un solo uso |
| expires_at | datetime | caducidad |

### `admin_users` — acceso al panel
| id | UUID PK · email · hashed_password (bcrypt) · role |

---

## 3. API (FastAPI) — endpoints

### Público
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/leads` | Registra lead, valida cédula/consentimiento, genera cupón, dispara email SendGrid, crea magic link. |
| GET  | `/api/ruleta/config` | Devuelve segmentos visibles de la ruleta (nombre + color, **sin** probabilidades). |
| POST | `/api/ruleta/spin` | Valida magic link (1 uso), **decide premio en backend**, descuenta stock, firma JWT, envía 2º email. Devuelve índice del segmento ganador para animar. |
| GET  | `/api/magic/{token}` | Valida el magic link antes de mostrar la ruleta. |

### Admin (protegido con JWT de sesión)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/admin/login` | Login → token de sesión. |
| GET  | `/api/admin/metrics` | Total participantes, premios entregados vs disponibles, giros, tasa de conversión. |
| GET/POST/PUT/DELETE | `/api/admin/prizes` | CRUD de premios (alimenta la ruleta dinámicamente). |
| GET  | `/api/admin/leads` | Listado + export CSV. |
| POST | `/api/admin/redeem` | Recibe el QR escaneado, **verifica firma JWT**, marca `redeemed`, devuelve validez + premio. |

---

## 4. Flujo de QRs encriptados (JWT)

Dos QRs firmados con `PyJWT` (secreto `JWT_SECRET`, algoritmo HS256):

**A) QR del cupón (email 1):**
```json
{ "typ": "coupon", "lead_id": "...", "code": "CERRITOS-10-XXXX", "exp": <caducidad> }
```

**B) QR del premio (email 2, tras ganar):**
```json
{ "typ": "prize", "spin_id": "...", "lead_id": "...",
  "prize": "Taladro Bosch", "cedula_last4": "1234", "exp": <caducidad> }
```

**Validación en tienda (`/admin/escanear`):** la cámara lee el QR → `POST /api/admin/redeem`
→ backend verifica firma + expiración + que **no haya sido redimido antes** → responde
`{ valido, premio, ya_redimido }`. Anti-fraude: un premio no se puede entregar dos veces.

**Provably fair:** cada `spin` guarda un `server_seed` firmado; se puede auditar que el
resultado no se manipuló.

---

## 5. Estructura de carpetas

```
inauguracion-cerritos/
├── README_PLAN.md            ← este documento
├── docker-compose.yml        ← orquesta backend + frontend (+ postgres en local)
├── secret.toml               ← SECRETOS (git-ignored, nunca push) — lo provees tú
├── .env.example              ← plantilla de variables (sin valores)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/              ← migraciones
│   ├── app/
│   │   ├── main.py           ← FastAPI app
│   │   ├── config.py         ← lee variables de entorno
│   │   ├── database.py       ← SQLAlchemy engine/session
│   │   ├── models/           ← Lead, Prize, Spin, MagicLink, AdminUser
│   │   ├── schemas/          ← Pydantic
│   │   ├── routers/          ← leads, ruleta, admin, magic
│   │   ├── services/         ← ruleta (peso+stock), sendgrid, jwt_qr, referrals
│   │   └── security.py       ← hashing, auth admin
│   └── seed.py               ← premios iniciales + admin
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.ts
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx          ← landing de la campaña
    │   ├── registro/         ← formulario (Nombre, Tel, Correo, Cédula, Dirección + consentimiento)
    │   ├── exito/            ← cupón en pantalla + botón wa.me (auto-envío magic link)
    │   ├── ruleta/           ← ruleta Framer Motion (valida magic link)
    │   └── admin/
    │       ├── page.tsx      ← dashboard de métricas
    │       ├── premios/      ← CRUD de inventario
    │       └── escanear/     ← lector QR con cámara (html5-qrcode)
    ├── components/ui/        ← Shadcn UI
    └── lib/api.ts            ← cliente del backend
```

---

## 6. Seguridad y cumplimiento
- **Ley 1581 / Habeas Data (Colombia):** checkbox de consentimiento obligatorio + política
  de tratamiento de datos antes de enviar el formulario. Se guarda sello de tiempo.
- Ruleta y premios decididos **solo en backend**.
- Magic links de **un solo uso** con caducidad.
- QRs de premio **no reutilizables** (marca de redención).
- Secretos **nunca** en el repo (`secret.toml` en `.gitignore`; en Coolify van como env vars).
- Admin protegido con contraseña hasheada (bcrypt) + token de sesión.

---

## 7. Variables de entorno (mapeo desde `secret.toml`)

| Variable | Origen | Uso |
|---|---|---|
| `DATABASE_URL` | Coolify Postgres | conexión DB |
| `SENDGRID_API_KEY` | tu SendGrid | emails |
| `SENDGRID_FROM_EMAIL` | remitente verificado | emails |
| `JWT_SECRET` | genero uno fuerte | firma de QRs |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | tú defines | acceso panel |
| `PUBLIC_BASE_URL` | `https://cerritos.tudominio.com` | magic links, QRs |
| `NEXT_PUBLIC_API_URL` | URL del backend | frontend → backend |

---

## 8. Plan de entrega por fases
- **F1 – Cimientos:** repo (subcarpeta) + Docker + Postgres + FastAPI (modelos, Alembic,
  `POST /leads`, lógica segura de ruleta). Desplegable en Coolify.
- **F2 – Comunicaciones:** SendGrid + generación de QR + JWT + magic link wa.me.
- **F3 – Público:** Next.js + Tailwind + Shadcn + Framer Motion (formulario, éxito, ruleta).
- **F4 – Admin:** dashboard + CRUD premios + escáner QR con cámara.
- **F5 – Deploy:** Dockerfiles optimizados + `docker-compose` + subdominio + env vars en Coolify.

---

## 9. Innovación incluida
1. Cumplimiento Habeas Data (consentimiento auditable).
2. Anti-fraude de canje (QR premio de un solo uso, con hora y responsable).
3. Sistema de **referidos** (giro extra por invitar).
4. Ruleta **provably-fair** (semilla firmada auditable).
5. Dashboard en **tiempo real** para proyectar el día del evento.
6. Export CSV + resumen post-evento.
