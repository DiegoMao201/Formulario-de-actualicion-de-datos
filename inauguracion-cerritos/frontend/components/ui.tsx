"use client";
import clsx from "clsx";
import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "yellow" | "ghost" | "outline";
}) {
  const styles = {
    primary: "bg-navy text-white hover:bg-navy-light",
    yellow: "bg-brand-yellow text-navy hover:brightness-95",
    ghost: "bg-white/10 text-white hover:bg-white/20",
    outline: "border border-navy/20 text-navy hover:bg-navy/5",
  }[variant];
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
        styles,
        className
      )}
      {...props}
    />
  );
}

export function Input({
  className,
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <label className="block">
      {label && <span className="mb-1.5 block text-sm font-medium text-navy">{label}</span>}
      <input
        className={clsx(
          "w-full rounded-xl border border-navy/15 bg-white px-4 py-3 text-navy outline-none transition placeholder:text-navy/30 focus:border-navy focus:ring-2 focus:ring-navy/15",
          className
        )}
        {...props}
      />
    </label>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={clsx("rounded-2xl bg-white p-6 shadow-card", className)}>{children}</div>
  );
}

export function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl pintuco-flame shadow-glow">
        <span className="text-lg">🎨</span>
      </div>
      <div className="leading-tight">
        <div className={clsx("text-[11px] tracking-[0.25em]", dark ? "text-white/70" : "text-navy/60")}>
          TIENDA PINTUCO
        </div>
        <div className={clsx("text-lg font-extrabold", dark ? "text-brand-yellow" : "text-navy")}>
          CERRITOS
        </div>
      </div>
    </div>
  );
}
