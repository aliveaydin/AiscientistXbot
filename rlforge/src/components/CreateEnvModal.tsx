"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { CreateEnvForm } from "./CreateEnvForm";

export function CreateEnvModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-black border border-[#1a1a1a] rounded-xl w-full max-w-2xl mx-4 max-h-[85vh] overflow-y-auto p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#666] hover:text-white transition-colors"
        >
          <X size={18} />
        </button>
        <h2 className="text-xl font-bold text-white mb-1">New Environment</h2>
        <p className="text-sm text-[#888] mb-6">
          Describe the RL environment you want in natural language.
        </p>
        <CreateEnvForm />
      </div>
    </div>
  );
}
