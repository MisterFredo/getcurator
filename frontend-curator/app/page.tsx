"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/* =========================================================
   🔥 REDIRECT HOME → FEED
========================================================= */

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/news");
  }, [router]);

  return null;
}

/* =========================================================
   📦 ANCIENNE PAGE HOME (ONBOARDING)
   → conservée pour réactivation future
========================================================= */

/*
"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

// STEPS
import StepTopics from "@/components/home/StepTopics";
import StepSources from "@/components/home/StepSources";
import StepCompanies from "@/components/home/StepCompanies";
import StepChaos from "@/components/home/StepChaos";

export default function Home() {
  const [step, setStep] = useState(0);

  const [topics, setTopics] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);

  // =========================
  // FETCH DATA
  // =========================
  useEffect(() => {
    async function load() {
      try {
        const t = await api.get("/topic/list");
        const s = await api.get("/source/list");
        const c = await api.get("/company/list");

        setTopics(t.topics || []);
        setSources(s.sources || []);
        setCompanies(c.companies || []);
      } catch (e) {
        console.error("❌ LOAD ERROR", e);
      }
    }

    load();
  }, []);

  // =========================
  // NAVIGATION
  // =========================
  function handleNext() {
    setStep((s) => Math.min(s + 1, 3));
  }

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight") handleNext();
    }

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  return (
    <div className="w-full min-h-screen bg-white px-10 py-10">

      {step === 0 && <StepTopics topics={topics} />}
      {step === 1 && <StepSources sources={sources} />}
      {step === 2 && <StepCompanies companies={companies} />}
      {step === 3 && (
        <StepChaos
          companies={companies}
          sources={sources}
        />
      )}

      {step !== 3 && (
        <div className="flex justify-center mt-12">
          <button
            onClick={handleNext}
            className="px-6 py-3 bg-black text-white rounded-lg"
          >
            Next →
          </button>
        </div>
      )}

    </div>
  );
}
*/
