"use client";

import { UserProfile } from "@clerk/nextjs";
import { dark } from "@clerk/themes";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-sm text-[#888] mt-1">
          Manage your profile, connected accounts, and security.
        </p>
      </div>

      <div className="[&_.cl-rootBox]:w-full [&_.cl-card]:bg-transparent [&_.cl-card]:shadow-none [&_.cl-card]:border-0 [&_.cl-navbar]:hidden [&_.cl-pageScrollBox]:p-0">
        <UserProfile
          appearance={{
            baseTheme: dark,
            variables: {
              colorPrimary: "#ffffff",
              colorBackground: "#000000",
              colorInputBackground: "#111111",
              colorInputText: "#f5f5f5",
              colorText: "#f5f5f5",
              colorTextSecondary: "#888888",
              colorNeutral: "#888888",
            },
            elements: {
              rootBox: "w-full",
              card: "bg-transparent shadow-none border-0 w-full",
              navbar: "hidden",
              pageScrollBox: "p-0",
              page: "gap-4",
            },
          }}
        />
      </div>
    </div>
  );
}
