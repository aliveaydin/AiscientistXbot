"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { LayoutDashboard, Box, Cpu, FlaskConical, User } from "lucide-react";

const sidebarLinks = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/environments", label: "Environments", icon: Box },
  { href: "/dashboard/training", label: "Training", icon: Cpu },
  { href: "/dashboard/research", label: "Research", icon: FlaskConical },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, isLoaded } = useUser();

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname.startsWith(href);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-[#1a1a1a] bg-black hidden md:flex flex-col py-6 px-3 shrink-0">
        {/* User info */}
        <div className="flex items-center gap-3 px-3 mb-8">
          {isLoaded && user?.imageUrl ? (
            <img
              src={user.imageUrl}
              alt=""
              className="w-9 h-9 rounded-full border border-[#222]"
            />
          ) : (
            <div className="w-9 h-9 rounded-full bg-[#1a1a1a] flex items-center justify-center">
              <User className="w-4 h-4 text-[#555]" />
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {isLoaded ? (user?.firstName || user?.username || "User") : "..."}
            </p>
            <p className="text-[10px] text-[#666] truncate">
              {isLoaded ? user?.primaryEmailAddress?.emailAddress : ""}
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          {sidebarLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.href, link.exact);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  active
                    ? "bg-[#111] text-white"
                    : "text-[#888] hover:text-white hover:bg-[#0a0a0a]"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {link.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Mobile nav */}
      <div className="md:hidden flex border-b border-[#1a1a1a] bg-black overflow-x-auto px-4 py-2 gap-1">
        {sidebarLinks.map((link) => {
          const Icon = link.icon;
          const active = isActive(link.href, link.exact);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs whitespace-nowrap transition-colors ${
                active ? "bg-[#111] text-white" : "text-[#888]"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-6 py-8">
          {children}
        </div>
      </div>
    </div>
  );
}
