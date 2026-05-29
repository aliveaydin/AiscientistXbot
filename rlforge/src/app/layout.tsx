import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CreditProvider } from "@/components/CreditProvider";

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
          colorBackground: "#0a0a0a",
          colorInputBackground: "#18181b",
          colorInputText: "#ffffff",
          colorText: "#ffffff",
          colorTextOnPrimaryBackground: "#000000",
          colorTextSecondary: "#a1a1aa",
          colorNeutral: "#ffffff",
          colorDanger: "#ef4444",
          borderRadius: "0.5rem",
          fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
        },
        elements: {
          card: "bg-[#0a0a0a] border border-[#27272a] shadow-2xl",
          headerTitle: "text-white font-bold text-xl",
          headerSubtitle: "text-[#a1a1aa]",
          socialButtonsBlockButton: "bg-[#18181b] border border-[#3f3f46] text-white hover:bg-[#27272a] hover:border-[#52525b] transition-all",
          socialButtonsBlockButtonText: "text-white font-medium",
          formFieldLabel: "text-[#d4d4d8]",
          formFieldInput: "bg-[#18181b] border-[#3f3f46] text-white placeholder:text-[#71717a] focus:border-[#a1a1aa] focus:ring-1 focus:ring-[#a1a1aa]",
          formButtonPrimary: "bg-white text-black hover:bg-[#e4e4e7] font-semibold",
          footerActionLink: "text-white font-semibold hover:text-[#d4d4d8]",
          footerActionText: "text-[#a1a1aa]",
          dividerLine: "bg-[#27272a]",
          dividerText: "text-[#71717a]",
          formFieldAction: "text-[#a1a1aa] hover:text-white",
          identityPreviewEditButton: "text-[#a1a1aa] hover:text-white",
          userButtonPopoverCard: "bg-[#0a0a0a] border border-[#27272a]",
          userButtonPopoverActionButton: "text-[#d4d4d8] hover:bg-[#18181b]",
          userButtonPopoverActionButtonText: "text-[#d4d4d8]",
          userButtonPopoverFooter: "border-t border-[#27272a]",
          userPreviewMainIdentifier: "text-white",
          userPreviewSecondaryIdentifier: "text-[#a1a1aa]",
        },
      }}
    >
      <html lang="en" className="dark">
        <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-[#f5f5f5] min-h-screen flex flex-col`}>
          <CreditProvider>
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </CreditProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
