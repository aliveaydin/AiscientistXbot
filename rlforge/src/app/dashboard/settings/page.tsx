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
