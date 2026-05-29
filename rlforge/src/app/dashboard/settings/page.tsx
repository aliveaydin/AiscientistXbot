"use client";

import { useState, useEffect } from "react";
import { UserProfile, useAuth } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import { User, Shield, CreditCard, Bell, Loader2 } from "lucide-react";
import SubscriptionTab from "./SubscriptionTab";
import { getEmailPreferences, updateEmailPreferences } from "@/lib/api";

const tabs = [
  { id: "profile", label: "Profile & Security", icon: User },
  { id: "subscription", label: "Subscription", icon: CreditCard },
  { id: "notifications", label: "Notifications", icon: Bell },
];

function NotificationsTab() {
  const { getToken } = useAuth();
  const [prefs, setPrefs] = useState({ email_notifications: true, marketing_emails: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await getEmailPreferences(token);
        setPrefs({
          email_notifications: data.email_notifications ?? true,
          marketing_emails: data.marketing_emails ?? true,
        });
      } catch {
        // defaults stay
      }
      setLoading(false);
    })();
  }, [getToken]);

  const toggle = async (key: "email_notifications" | "marketing_emails") => {
    const newVal = !prefs[key];
    setPrefs((p) => ({ ...p, [key]: newVal }));
    setSaving(true);
    try {
      const token = await getToken();
      if (token) await updateEmailPreferences(token, { [key]: newVal });
    } catch {
      setPrefs((p) => ({ ...p, [key]: !newVal }));
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-[#666]" />
      </div>
    );
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h3 className="text-white font-semibold text-sm mb-1">Email Notifications</h3>
        <p className="text-[#666] text-xs">Choose which emails you want to receive from kualia.ai.</p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4">
          <div>
            <p className="text-white text-sm font-medium">System notifications</p>
            <p className="text-[#666] text-xs mt-0.5">
              Training complete, paper ready, environment generated, low credits
            </p>
          </div>
          <button
            onClick={() => toggle("email_notifications")}
            className={`relative w-11 h-6 rounded-full transition-colors ${
              prefs.email_notifications ? "bg-white" : "bg-[#333]"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-transform ${
                prefs.email_notifications
                  ? "translate-x-5 bg-black"
                  : "translate-x-0 bg-[#666]"
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-4">
          <div>
            <p className="text-white text-sm font-medium">Product updates & tips</p>
            <p className="text-[#666] text-xs mt-0.5">
              New features, RL tips, and platform updates
            </p>
          </div>
          <button
            onClick={() => toggle("marketing_emails")}
            className={`relative w-11 h-6 rounded-full transition-colors ${
              prefs.marketing_emails ? "bg-white" : "bg-[#333]"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-transform ${
                prefs.marketing_emails
                  ? "translate-x-5 bg-black"
                  : "translate-x-0 bg-[#666]"
              }`}
            />
          </button>
        </div>
      </div>

      {saving && (
        <p className="text-xs text-[#666] flex items-center gap-1">
          <Loader2 className="w-3 h-3 animate-spin" /> Saving...
        </p>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-sm text-[#888] mt-1">
          Manage your profile, subscription, and security.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-[#1a1a1a]">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? "border-white text-white"
                  : "border-transparent text-[#666] hover:text-[#aaa]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Profile & Security (Clerk) */}
      {activeTab === "profile" && (
        <div className="clerk-profile-override">
          <UserProfile
            appearance={{
              baseTheme: dark,
              variables: {
                colorPrimary: "#ffffff",
                colorBackground: "#000000",
                colorInputBackground: "#111111",
                colorInputText: "#f5f5f5",
                colorText: "#f5f5f5",
                colorTextSecondary: "#cccccc",
                colorNeutral: "#f5f5f5",
                colorTextOnPrimaryBackground: "#000000",
              },
              elements: {
                rootBox: "w-full",
                card: "bg-transparent shadow-none border-0 w-full",
                navbar: "bg-transparent border-r border-[#1a1a1a]",
                navbarButton: "text-[#bbb] hover:text-white data-[active=true]:text-white",
                navbarButtonIcon: "text-[#bbb]",
                pageScrollBox: "p-0",
                page: "gap-4",
                headerTitle: "text-white",
                headerSubtitle: "text-[#888]",
                profilePage: "gap-6",
                profileSectionTitle: "border-b border-[#1a1a1a]",
                profileSectionTitleText: "text-white text-sm font-semibold",
                profileSectionPrimaryButton: "text-white hover:text-white",
                profileSectionContent: "text-[#ccc]",
                formFieldLabel: "text-[#999]",
                formFieldInput: "bg-[#111] border-[#222] text-white",
                formButtonPrimary: "bg-white text-black hover:bg-[#ddd]",
                formButtonReset: "text-[#888] hover:text-white",
                badge: "bg-[#1a1a1a] text-[#999] border-[#222]",
                avatarBox: "border border-[#222]",
                accordionTriggerButton: "text-[#ccc] hover:text-white",
                menuButton: "text-[#888] hover:text-white",
                menuList: "bg-[#111] border-[#222]",
                menuItem: "text-[#ccc] hover:text-white hover:bg-[#1a1a1a]",
                userPreviewMainIdentifier: "text-white",
                userPreviewSecondaryIdentifier: "text-[#888]",
                breadcrumbs: "text-[#888]",
                breadcrumbsItem: "text-[#888]",
                breadcrumbsItemDivider: "text-[#555]",
                modalCloseButton: "text-[#888] hover:text-white",
                footer: "hidden",
              },
            }}
          />
        </div>
      )}

      {/* Subscription */}
      {activeTab === "subscription" && <SubscriptionTab />}

      {/* Notifications */}
      {activeTab === "notifications" && <NotificationsTab />}

      <style jsx global>{`
        .clerk-profile-override .cl-internal-b3fm6y,
        .clerk-profile-override .cl-internal-1hp5nqm,
        .clerk-profile-override [class*="cl-internal"] {
          color: inherit;
        }
        .clerk-profile-override .cl-profileSection__profile .cl-profileSectionContent,
        .clerk-profile-override .cl-profileSection__emailAddresses .cl-profileSectionContent,
        .clerk-profile-override .cl-profileSection__connectedAccounts .cl-profileSectionContent {
          color: #ccc;
        }
        .clerk-profile-override p,
        .clerk-profile-override span,
        .clerk-profile-override label,
        .clerk-profile-override h1,
        .clerk-profile-override h2,
        .clerk-profile-override h3 {
          color: inherit;
        }
        .clerk-profile-override .cl-navbar {
          background: transparent !important;
        }
        .clerk-profile-override .cl-navbarButton {
          color: #bbb !important;
        }
        .clerk-profile-override .cl-navbarButton[data-active="true"],
        .clerk-profile-override .cl-navbarButton:hover {
          color: #fff !important;
        }
        .clerk-profile-override .cl-headerTitle {
          color: #fff !important;
        }
        .clerk-profile-override .cl-headerSubtitle {
          color: #888 !important;
        }
        .clerk-profile-override .cl-profileSectionTitleText {
          color: #fff !important;
        }
        .clerk-profile-override .cl-profileSectionContent__profile,
        .clerk-profile-override .cl-profileSectionContent__emailAddresses,
        .clerk-profile-override .cl-profileSectionContent__connectedAccounts {
          color: #ccc !important;
        }
        .clerk-profile-override .cl-userPreview__userProfile .cl-userPreviewMainIdentifier {
          color: #fff !important;
        }
        .clerk-profile-override .cl-badge {
          color: #999 !important;
          background: #1a1a1a !important;
        }
        .clerk-profile-override .cl-profileSectionPrimaryButton,
        .clerk-profile-override .cl-accordionTriggerButton,
        .clerk-profile-override .cl-menuButton {
          color: #bbb !important;
        }
        .clerk-profile-override .cl-profileSectionPrimaryButton:hover,
        .clerk-profile-override .cl-accordionTriggerButton:hover,
        .clerk-profile-override .cl-menuButton:hover {
          color: #fff !important;
        }
        .clerk-profile-override .cl-internal-b3fm6y {
          color: #ccc !important;
        }
        .clerk-profile-override .cl-formFieldLabel {
          color: #999 !important;
        }
        .clerk-profile-override .cl-card {
          background: transparent !important;
          box-shadow: none !important;
        }
        .clerk-profile-override .cl-footer {
          display: none !important;
        }
      `}</style>
    </div>
  );
}
