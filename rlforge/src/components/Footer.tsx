"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";

const columns = [
  {
    title: "Product",
    links: [
      { href: "/environments", label: "Environment Generation" },
      { href: "/research", label: "Research Lab" },
      { href: "/catalog", label: "Template Catalog" },
      { href: "/blog", label: "Blog" },
    ],
  },
  {
    title: "Developers",
    links: [
      { href: "/docs", label: "Documentation" },
      { href: "/docs#python-sdk", label: "Python SDK" },
      { href: "/docs#api-reference", label: "API Reference" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/sign-up", label: "Get Started" },
      { href: "/sign-in", label: "Sign In" },
    ],
  },
];

export function Footer() {
  const { isSignedIn } = useAuth();
  if (isSignedIn) return null;

  return (
    <footer className="border-t border-[#1a1a1a] mt-24">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div>
            <p className="font-bold text-white mb-2">kualia.ai</p>
            <p className="text-sm text-[#888] leading-relaxed">
              Generate RL environments, train agents, run experiments, and create research papers — all in one platform.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <p className="text-sm font-medium text-[#888] mb-3">{col.title}</p>
              <ul className="space-y-2">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-[#666] hover:text-white transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-[#1a1a1a] pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-[#555]">
            By <span className="text-[#888]">Kualia AI</span>
          </p>
          <p className="text-xs text-[#555]">&copy; {new Date().getFullYear()} kualia.ai. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
