import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/providers";

export const metadata: Metadata = {
  title: "FactorTrace",
  description: "Global Regulatory Emissions Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* Use standard system fonts instead of missing local files */}
      <body className="antialiased bg-slate-50 text-slate-900 font-sans">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
