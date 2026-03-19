"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useAuth, SignInButton, UserButton } from "@clerk/nextjs";

const publicLinks = [
  { href: "/environments", label: "Environments" },
  { href: "/blog", label: "Blog" },
  { href: "/research", label: "Research Lab" },
  { href: "/docs", label: "Docs" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { isSignedIn, isLoaded } = useAuth();

  const logoHref = isSignedIn ? "/dashboard" : "/";
  const navLinks = isSignedIn ? [] : publicLinks;

  return (
    <nav className="border-b border-[#1a1a1a] bg-black/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href={logoHref} className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight text-white">kualia</span>
          <span className="text-[10px] text-[#555] font-mono mt-1">.ai</span>
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
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8",
                },
              }}
            />
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
        <div className="md:hidden border-t border-[#1a1a1a] px-6 py-4 space-y-3">
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
              <UserButton
                appearance={{
                  elements: {
                    avatarBox: "w-8 h-8",
                  },
                }}
              />
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
