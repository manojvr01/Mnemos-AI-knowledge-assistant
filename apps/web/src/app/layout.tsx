import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mnemos — AI Knowledge Assistant",
  description: "Your knowledge. Searchable. Understandable. Verifiable. Enterprise RAG with deterministic, verifiable citations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0B0F19] text-[#F9FAFB] antialiased">
        {children}
      </body>
    </html>
  );
}
