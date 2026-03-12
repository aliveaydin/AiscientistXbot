import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Kualia.ai — Robotics & AI Research Lab",
    template: "%s | Kualia.ai",
  },
  description:
    "Advancing robotics through reinforcement learning, environment design, and autonomous research. We build intelligent systems that learn to interact with the physical world.",
  keywords: [
    "robotics",
    "reinforcement learning",
    "AI research",
    "RL environments",
    "machine learning",
    "autonomous systems",
    "robot learning",
  ],
  openGraph: {
    title: "Kualia.ai — Robotics & AI Research Lab",
    description:
      "Advancing robotics through reinforcement learning, environment design, and autonomous research.",
    url: "https://kualia.ai",
    siteName: "Kualia.ai",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kualia.ai — Robotics & AI Research Lab",
    description:
      "Advancing robotics through reinforcement learning, environment design, and autonomous research.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-[#f5f5f5] min-h-screen flex flex-col`}
      >
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
