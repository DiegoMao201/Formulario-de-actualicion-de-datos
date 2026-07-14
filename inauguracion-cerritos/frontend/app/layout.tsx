import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tienda Pintuco Cerritos — ¡Inauguración!",
  description:
    "Regístrate en la inauguración de la nueva Tienda Pintuco Cerritos, recibe tu cupón y gira la ruleta del equipo ganador Pintuco.",
};

export const viewport: Viewport = {
  themeColor: "#0A2E57",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
