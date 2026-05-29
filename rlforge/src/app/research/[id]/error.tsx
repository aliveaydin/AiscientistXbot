"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ResearchError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Research Lab error:", error);
  }, [error]);

  return (
    <div className="flex items-center justify-center py-24 px-4">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-white mb-2">Research Lab Error</h2>
        <p className="text-sm text-[#888] mb-6">
          {error.message || "Failed to load the research project."}
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="flex items-center gap-2 px-4 py-2 bg-white text-black text-sm font-medium rounded-md hover:bg-[#e0e0e0] transition-colors"
          >
            <RotateCcw className="w-4 h-4" /> Try Again
          </button>
          <Link
            href="/dashboard/research"
            className="flex items-center gap-2 px-4 py-2 border border-[#333] text-sm text-[#888] rounded-md hover:text-white hover:border-[#555] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Research Projects
          </Link>
        </div>
      </div>
    </div>
  );
}
