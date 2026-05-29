"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X, Zap } from "lucide-react";
import { useAuth, SignInButton, UserButton } from "@clerk/nextjs";
import { useCreditInfo } from "./CreditProvider";

const publicLinks = [
  { href: "/environments", label: "Environment Generation" },
  { href: "/research", label: "Research Lab" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Documentation" },
  { href: "/blog", label: "Blog" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { isSignedIn, isLoaded } = useAuth();
  const { balance, plan, loading: creditsLoading } = useCreditInfo();

  const logoHref = isSignedIn ? "/dashboard" : "/";
  const navLinks = isSignedIn ? [] : publicLinks;

  return (
    <nav className="border-b border-[#1a1a1a] bg-black/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
        <Link href={logoHref} className="flex items-center gap-1.5">
          <img src="/logo.svg" alt="Kualia" className="h-8 w-8" />
          <span className="text-[22px] font-extrabold tracking-tight text-white leading-none">kualia</span>
          <span className="text-xs text-[#666] font-light tracking-wide ml-0.5">.ai</span>
        </Link>

        {navLinks.length > 0 && (
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`text-sm transition-colors ${
                  pathname.startsWith(l.href)
                    ? "text-white"
                    : "text-[#888] hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>
        )}

        <div className="hidden md:flex items-center gap-4">
          {isLoaded && !isSignedIn && (
            <SignInButton mode="modal">
              <button className="text-sm text-[#888] hover:text-white transition-colors">
                Sign In
              </button>
            </SignInButton>
          )}
          {isLoaded && isSignedIn && (
            <>
              <Link
                href="/dashboard"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg hover:border-[#3a3a3a] transition-colors"
                title={`${plan?.display_name || "Free"} plan`}
              >
                <Zap size={14} className="text-yellow-400" />
                <span className="text-sm font-medium text-white">
                  {creditsLoading ? "..." : `$${balance.toFixed(2)}`}
                </span>
              </Link>
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "w-8 h-8",
                  },
                }}
              />
            </>
          )}
        </div>

        <button
          className="md:hidden text-[#888] hover:text-white"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-[#1a1a1a] px-4 py-4 space-y-3">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={`block text-sm ${
                pathname.startsWith(l.href) ? "text-white" : "text-[#888]"
              }`}
            >
              {l.label}
            </Link>
          ))}
          <div className={`${navLinks.length > 0 ? "pt-3 border-t border-[#1a1a1a]" : ""}`}>
            {isLoaded && !isSignedIn && (
              <SignInButton mode="modal">
                <button className="text-sm text-[#888] hover:text-white">
                  Sign In
                </button>
              </SignInButton>
            )}
            {isLoaded && isSignedIn && (
              <div className="flex items-center gap-4">
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg"
                >
                  <Zap size={14} className="text-yellow-400" />
                  <span className="text-sm font-medium text-white">
                    {creditsLoading ? "..." : `$${balance.toFixed(2)}`}
                  </span>
                  <span className="text-xs text-[#666] ml-1">{plan?.display_name || "Free"}</span>
                </Link>
                <UserButton
                  appearance={{
                    elements: {
                      avatarBox: "w-8 h-8",
                    },
                  }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
