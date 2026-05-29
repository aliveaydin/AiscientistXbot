"use client";
import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { useAuth } from "@clerk/nextjs";

interface CreditInfo {
  balance: number;
  plan: {
    name: string;
    display_name: string;
    price_monthly: number;
    monthly_credits: number;
    max_environments: number;
    max_training_steps: number;
    pdf_download: boolean;
    github_export: boolean;
  } | null;
  monthly_usage: {
    total_spent: number;
    by_operation: Record<string, number>;
  } | null;
  loading: boolean;
  refresh: () => void;
}

const CreditContext = createContext<CreditInfo>({
  balance: 0,
  plan: null,
  monthly_usage: null,
  loading: true,
  refresh: () => {},
});

export function useCreditInfo() {
  return useContext(CreditContext);
}

export function CreditProvider({ children }: { children: ReactNode }) {
  const { isSignedIn, getToken } = useAuth();
  const [balance, setBalance] = useState(0);
  const [plan, setPlan] = useState<CreditInfo["plan"]>(null);
  const [monthlyUsage, setMonthlyUsage] = useState<CreditInfo["monthly_usage"]>(null);
  const [loading, setLoading] = useState(true);

  const fetchCredits = useCallback(async () => {
    if (!isSignedIn) {
      setLoading(false);
      return;
    }
    try {
      const token = await getToken();
      const res = await fetch("/api/users/me/credits", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance || 0);
        setPlan(data.plan || null);
        setMonthlyUsage(data.monthly_usage || null);
      }
    } catch (e) {
      console.error("Failed to fetch credits:", e);
    } finally {
      setLoading(false);
    }
  }, [isSignedIn, getToken]);

  useEffect(() => {
    fetchCredits();
    const interval = setInterval(fetchCredits, 60000);
    return () => clearInterval(interval);
  }, [fetchCredits]);

  return (
    <CreditContext.Provider
      value={{ balance, plan, monthly_usage: monthlyUsage, loading, refresh: fetchCredits }}
    >
      {children}
    </CreditContext.Provider>
  );
}
