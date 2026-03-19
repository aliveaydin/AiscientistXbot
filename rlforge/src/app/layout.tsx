import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "kualia.ai — The RL Experiment Platform",
    template: "%s | kualia.ai",
  },
  description:
    "Design, build, train, and experiment with reinforcement learning environments. AI-powered generation, iterative builder, agent training, and experiment tracking.",
  keywords: [
    "reinforcement learning", "rl environments", "gymnasium", "ai",
    "environment generation", "stable baselines3", "agent training",
    "experiment tracking", "rl platform", "robotics", "machine learning",
    "kualia", "rl builder", "ppo", "sac", "dqn",
  ],
  openGraph: {
    title: "kualia.ai — The RL Experiment Platform",
    description: "Design, build, train, and experiment with RL environments. From idea to trained agent.",
    url: "https://kualia.ai",
    siteName: "kualia.ai",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "kualia.ai — The RL Experiment Platform",
    description: "Design, build, train, and experiment with RL environments. From idea to trained agent.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorPrimary: "#ffffff",
          colorBackground: "#111111",
          colorInputBackground: "#1a1a1a",
          colorInputText: "#f5f5f5",
          colorText: "#f5f5f5",
          colorTextSecondary: "#888888",
          colorNeutral: "#888888",
        },
      }}
    >
      <html lang="en" className="dark">
        <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-[#f5f5f5] min-h-screen flex flex-col`}>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </body>
      </html>
    </ClerkProvider>
  );
}
