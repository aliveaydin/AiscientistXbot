import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-16 md:py-24">
      <h1 className="text-3xl font-bold text-white mb-2">Privacy Policy</h1>
      <p className="text-sm text-[#555] mb-12">Last updated: March 2026</p>

      <div className="prose-custom space-y-8 text-[#ccc] text-sm leading-relaxed">
        <Section title="1. Information We Collect">
          <p className="font-medium text-white mt-2 mb-1">Account Information</p>
          <p>
            When you create an account via Clerk (our authentication provider), we collect your
            name, email address, profile picture, and linked account identifiers (Google or GitHub).
            We do not store your passwords — authentication is handled entirely by Clerk.
          </p>

          <p className="font-medium text-white mt-4 mb-1">Usage Data</p>
          <p>
            We collect information about how you use the Platform, including environments created,
            training runs executed, research projects initiated, and API requests made. This data
            is used to provide the service and improve the Platform.
          </p>

          <p className="font-medium text-white mt-4 mb-1">Generated Content</p>
          <p>
            We store the environments, trained models, training results, and research papers you
            create on the Platform. This data is necessary to provide the service and is associated
            with your account.
          </p>
        </Section>

        <Section title="2. How We Use Your Information">
          <ul className="list-disc pl-5 space-y-1">
            <li>To provide, maintain, and improve the Platform</li>
            <li>To authenticate your identity and manage your account</li>
            <li>To process your environment generation and training requests</li>
            <li>To enforce rate limits and prevent abuse</li>
            <li>To communicate important service updates</li>
            <li>To comply with legal obligations</li>
          </ul>
        </Section>

        <Section title="3. Third-Party Services">
          <p>We use the following third-party services that may process your data:</p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li>
              <strong className="text-white">Clerk</strong> — Authentication and user management.
              See{" "}
              <a href="https://clerk.com/privacy" target="_blank" rel="noopener noreferrer"
                className="text-white hover:underline">Clerk&apos;s Privacy Policy</a>.
            </li>
            <li>
              <strong className="text-white">OpenAI, Anthropic, Moonshot</strong> — AI model
              providers used for environment generation, research analysis, and paper writing.
              Your prompts and environment descriptions may be sent to these providers for processing.
            </li>
            <li>
              <strong className="text-white">Academic Sources</strong> — Academic paper metadata is fetched
              from public repositories for research reference purposes.
            </li>
            <li>
              <strong className="text-white">GitHub</strong> — If you use the GitHub export
              feature, environment code and models are sent to your GitHub account via the GitHub API.
            </li>
          </ul>
        </Section>

        <Section title="4. Data Storage and Security">
          <p>
            Your data is stored on secure servers hosted by Hetzner Online GmbH in Germany. We
            implement reasonable technical and organizational measures to protect your data against
            unauthorized access, alteration, or destruction. However, no method of transmission or
            storage is 100% secure.
          </p>
        </Section>

        <Section title="5. Data Retention">
          <p>
            We retain your data for as long as your account is active. If you delete your account,
            we will delete your personal data within 30 days, except where retention is required by
            law. Anonymized usage statistics may be retained indefinitely.
          </p>
        </Section>

        <Section title="6. Your Rights">
          <p>Depending on your jurisdiction, you may have the right to:</p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li><strong className="text-white">Access</strong> — Request a copy of your personal data</li>
            <li><strong className="text-white">Rectification</strong> — Correct inaccurate data</li>
            <li><strong className="text-white">Deletion</strong> — Request deletion of your data</li>
            <li><strong className="text-white">Portability</strong> — Receive your data in a portable format</li>
            <li><strong className="text-white">Objection</strong> — Object to certain processing activities</li>
          </ul>
          <p className="mt-2">
            To exercise these rights, contact us at{" "}
            <a href="mailto:privacy@kualia.ai" className="text-white hover:underline">
              privacy@kualia.ai
            </a>.
          </p>
        </Section>

        <Section title="7. Cookies">
          <p>
            The Platform uses essential cookies for authentication (managed by Clerk) and session
            management. We do not use tracking cookies or third-party advertising cookies.
          </p>
        </Section>

        <Section title="8. Children">
          <p>
            The Platform is not intended for children under 16. We do not knowingly collect data
            from children under 16. If you believe a child has provided us with personal data,
            please contact us.
          </p>
        </Section>

        <Section title="9. Changes to This Policy">
          <p>
            We may update this Privacy Policy from time to time. We will notify you of significant
            changes via email or a prominent notice on the Platform. Continued use after changes
            constitutes acceptance.
          </p>
        </Section>

        <Section title="10. Contact">
          <p>
            For privacy-related questions or requests, contact us at{" "}
            <a href="mailto:privacy@kualia.ai" className="text-white hover:underline">
              privacy@kualia.ai
            </a>.
          </p>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-base font-semibold text-white mb-3">{title}</h2>
      {children}
    </section>
  );
}
