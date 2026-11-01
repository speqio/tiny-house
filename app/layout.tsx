import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Tiny Houses Autosustentables · I+D PUCV",
  description:
    "Modelo de vivienda social modular con eficiencia hídrica y energía solar fotovoltaica para la Región de Valparaíso. Proyecto I+D, Facultad de Ingeniería PUCV.",
};

export const viewport: Viewport = {
  themeColor: "#090d16",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // suppressHydrationWarning: extensiones del navegador (p. ej. Scribe) inyectan atributos en <html>
    <html lang="es" className={`${sans.variable} ${mono.variable}`} suppressHydrationWarning>
      <body className="antialiased">{children}</body>
    </html>
  );
}
