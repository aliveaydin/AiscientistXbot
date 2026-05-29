import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <p className="text-6xl font-bold text-[#222] mb-4">404</p>
        <h2 className="text-lg font-semibold text-white mb-2">Page not found</h2>
        <p className="text-sm text-[#888] mb-6">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-black text-sm font-medium rounded-md hover:bg-[#e0e0e0] transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
