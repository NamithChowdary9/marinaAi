import type { Metadata, Viewport } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/layout/QueryProvider";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "MarineAI — Agentic Maritime Intelligence Platform",
  description:
    "Real-time ship tracking, ocean wave prediction, weather analysis, and AI-powered maritime decision support.",
  icons: { icon: "/favicon.ico" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#030d1a",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: "dark", background: "#030d1a" }}>
      <head>
        {/* Prevent white flash */}
        <style>{`html,body{background:#030d1a;color:#e2e8f0}`}</style>
        {/* Leaflet CSS — loaded via link to avoid SSR issues */}
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        {/* Fonts */}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-ocean-950 text-white antialiased font-sans">
        <QueryProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#0a2340",
                color: "#e2e8f0",
                border: "1px solid rgba(26,110,194,0.3)",
              },
            }}
          />
        </QueryProvider>
      </body>
    </html>
  );
}
