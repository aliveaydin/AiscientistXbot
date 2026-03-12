import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-[#1a1a1a] bg-black">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="h-6 w-6 rounded-md border border-[#333] flex items-center justify-center">
                <span className="text-[10px] font-bold font-mono text-white">
                  K
                </span>
              </div>
              <span className="text-sm font-semibold text-white">
                kualia<span className="text-[#666]">.ai</span>
              </span>
            </div>
            <p className="text-sm text-[#666] max-w-xs leading-relaxed">
              Advancing robotics through reinforcement learning, environment
              design, and autonomous research.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#666] mb-3">
              Platform
            </h4>
            <div className="space-y-2">
              <Link
                href="/research"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                Research
              </Link>
              <Link
                href="/environments"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                Environments
              </Link>
              <Link
                href="/blog"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                Blog
              </Link>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#666] mb-3">
              Connect
            </h4>
            <div className="space-y-2">
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                Twitter / X
              </a>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                GitHub
              </a>
              <Link
                href="/about"
                className="block text-sm text-[#888] hover:text-white transition-colors"
              >
                About
              </Link>
            </div>
          </div>
        </div>

        <div className="line-glow mt-8 mb-6" />

        <p className="text-xs text-[#555]">
          &copy; {new Date().getFullYear()} Kualia.ai. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
