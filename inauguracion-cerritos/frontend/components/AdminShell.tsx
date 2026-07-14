"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import { clearToken } from "@/lib/auth";

const NAV = [
  { href: "/admin", label: "Dashboard", icon: "📊" },
  { href: "/admin/premios", label: "Premios", icon: "🎁" },
  { href: "/admin/escanear", label: "Escanear QR", icon: "📷" },
];

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#EEF3F8]">
      <header className="sticky top-0 z-30 border-b border-navy/10 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg pintuco-flame text-sm">🎨</div>
            <span className="font-extrabold text-navy">Cerritos · Admin</span>
          </div>
          <button
            onClick={() => {
              clearToken();
              router.replace("/admin");
            }}
            className="text-sm font-medium text-navy/50 hover:text-brand-red"
          >
            Salir
          </button>
        </div>
        <nav className="mx-auto flex max-w-5xl gap-1 px-3 pb-2">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-sm font-medium transition",
                path === n.href ? "bg-navy text-white" : "text-navy/70 hover:bg-navy/5"
              )}
            >
              <span className="mr-1">{n.icon}</span>
              {n.label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-6">{children}</main>
    </div>
  );
}
