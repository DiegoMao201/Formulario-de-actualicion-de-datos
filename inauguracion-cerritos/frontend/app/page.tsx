import Link from "next/link";
import { Logo } from "@/components/ui";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-navy-dark text-white">
      {/* Imagen de fondo */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url(/fondo-inauguracion.jpg)" }}
      />
      {/* Overlay degradado para legibilidad */}
      <div className="absolute inset-0 bg-gradient-to-b from-navy/75 via-navy/80 to-navy-dark/95" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-3xl flex-col px-6 py-8">
        <header className="flex items-center justify-between">
          <Logo dark />
          <Link
            href="/admin"
            className="text-xs font-medium text-white/50 transition hover:text-white/80"
          >
            Admin
          </Link>
        </header>

        <section className="flex flex-1 flex-col items-center justify-center text-center">
          <span className="mb-4 inline-flex items-center gap-2 rounded-full bg-brand-yellow/15 px-4 py-1.5 text-sm font-semibold text-brand-yellow">
            🎉 ¡Ya abrimos!
          </span>
          <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
            Bienvenido a la nueva
            <br />
            <span className="text-flame">Tienda Pintuco Cerritos</span>
          </h1>
          <p className="mt-5 max-w-md text-white/70">
            Regístrate, recibe tu <strong className="text-white">cupón del 10%</strong> y gira la
            ruleta del <strong className="text-white">equipo ganador Pintuco</strong> 🏆 para ganar
            premios en la inauguración.
          </p>

          <Link
            href="/registro"
            className="mt-8 inline-flex items-center gap-2 rounded-2xl bg-brand-yellow px-8 py-4 text-lg font-bold text-navy shadow-glow transition hover:scale-105"
          >
            Participar ahora →
          </Link>

          <div className="mt-10 grid grid-cols-3 gap-4 text-center">
            {[
              { n: "1", t: "Regístrate" },
              { n: "2", t: "Recibe tu cupón" },
              { n: "3", t: "Gira y gana" },
            ].map((s) => (
              <div key={s.n} className="glass rounded-2xl px-4 py-5">
                <div className="mx-auto mb-2 flex h-9 w-9 items-center justify-center rounded-full bg-brand-yellow font-bold text-navy">
                  {s.n}
                </div>
                <div className="text-sm text-white/80">{s.t}</div>
              </div>
            ))}
          </div>
        </section>

        <footer className="pt-8 text-center text-xs text-white/40">
          Av. 30 de Agosto 105-42, Pereira · WhatsApp 310 280 66 05 · Ferreinox S.A.S. BIC
        </footer>
      </div>
    </main>
  );
}
