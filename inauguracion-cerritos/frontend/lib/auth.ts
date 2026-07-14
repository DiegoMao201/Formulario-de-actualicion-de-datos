"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const KEY = "cerritos_admin_token";

export function saveToken(t: string) {
  localStorage.setItem(KEY, t);
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(KEY);
}
export function clearToken() {
  localStorage.removeItem(KEY);
}

/** Protege una página admin: redirige a /admin si no hay sesión. */
export function useRequireAuth() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const t = getToken();
    if (!t) {
      router.replace("/admin");
      return;
    }
    setToken(t);
    setReady(true);
  }, [router]);
  return { token, ready };
}
