import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "OptiInfra - AI-Powered LLM Infrastructure Optimization",
  description: "Reduce costs by 50%, improve performance 3x, and ensure quality with intelligent multi-agent optimization",
  keywords: ["LLM", "infrastructure", "optimization", "AI", "cost reduction", "performance"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-50 antialiased">
        {children}
      </body>
    </html>
  );
}
