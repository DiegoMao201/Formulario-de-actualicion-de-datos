# 🎡 Tienda Pintuco Cerritos — Plataforma de Inauguración

Captación de leads + cupón 10% + ruleta de premios (resultado decidido en backend) +
panel de administración con escáner QR. **Independiente** del Portal de Vinculación (Streamlit).

- **Backend:** FastAPI + PostgreSQL + SendGrid + JWT
- **Frontend:** Next.js (App Router) + Tailwind + Framer Motion
- **Dominio:** `cerritos.ferreinox.co` (→ 192.81.216.49)

Ver [`README_PLAN.md`](./README_PLAN.md) para la arquitectura detallada.

---

## 🧪 Correr en local

```bash
cd inauguracion-cerritos
cp .env.example .env      # (ya generado con tus secretos; edítalo si quieres)
docker compose up --build
```

- Frontend: http://localhost:3000
- API + docs: http://localhost:8000/api/health · http://localhost:8000/docs
- Admin: http://localhost:3000/admin  (usuario/clave definidos en `.env`)

> Para que el frontend en local apunte a la API local, en `.env` deja
> `NEXT_PUBLIC_API_URL=http://localhost:8000` **antes** de `docker compose build`.

---

## 🚀 Despliegue en Coolify (contenedor aparte, mismo dominio)

> No toca el Streamlit existente: es un **recurso nuevo**. Base Directory apuntando a
> `inauguracion-cerritos/`.

### Opción recomendada — "Docker Compose" en Coolify
1. **New Resource → Docker Compose** en el mismo proyecto/servidor.
2. Repositorio: este repo. **Base Directory:** `inauguracion-cerritos`.
   Compose file: `docker-compose.yml`.
3. **Environment Variables:** pega el contenido de tu `.env` (Postgres, JWT, SendGrid, admin…).
   - Genera un `JWT_SECRET` largo (`openssl rand -hex 48`).
   - `NEXT_PUBLIC_API_URL=` (vacío) para usar rutas relativas `/api` en el mismo dominio.
4. **Dominios (Traefik gestionado por Coolify):**
   - Servicio **frontend** → `https://cerritos.ferreinox.co`
   - Servicio **backend** → `https://cerritos.ferreinox.co` con **Path** `/api`
     *(en Coolify: campo "Domains" del servicio backend = `https://cerritos.ferreinox.co/api`)*
5. Coolify pide certificado SSL (Let's Encrypt) automáticamente. Deploy.

### Alternativa — subdominio para la API (sin path routing)
1. Agrega DNS: `api-cerritos.ferreinox.co → 192.81.216.49`.
2. Backend → `https://api-cerritos.ferreinox.co`.
3. Build arg del frontend: `NEXT_PUBLIC_API_URL=https://api-cerritos.ferreinox.co`.
4. Asegura `CORS_ORIGINS=https://cerritos.ferreinox.co`.

### Base de datos
El compose incluye Postgres con volumen persistente (`pgdata`). Si prefieres la Postgres
gestionada de Coolify, crea el recurso y apunta `DATABASE_URL` a ella (quita el servicio `db`).

---

## 🔐 Seguridad y datos
- Resultado de la ruleta y validación de premios **siempre** en el backend.
- Magic link y QR de premio de **un solo uso**.
- Consentimiento **Habeas Data (Ley 1581)** obligatorio en el formulario.
- Secretos solo por variables de entorno (`.env` / `secrets.toml` están en `.gitignore`).

## 🎁 Configurar premios
Entra a `/admin` → **Premios**. La ruleta se alimenta dinámicamente de premios `activos`.
Al arrancar se siembran premios de ejemplo (edítalos o elimínalos). El peso `probabilidad`
es relativo (no tiene que sumar 1). Marca "Sigue participando" para el segmento sin premio.
