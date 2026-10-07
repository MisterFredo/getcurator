"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Instruction = {
  label: string;
  instruction: string;
  horizon?: "CURRENT" | "FUTURE";
};

type NegativePreference = {
  instruction: string;
  exceptions: string[];
};

type AdminProfile = {
  profile_editorial_text: string | null;
  profile_text: string | null;
  structured_profile: {
    watch_instructions: Instruction[];
    decision_lenses: Instruction[];
    negative_preferences: NegativePreference[];
  } | null;
};

type Props = {
  expertId: string;
  expertName?: string;
};

export default function TouchExpertProfileReminder({ expertId, expertName }: Props) {
  const [loaded, setLoaded] = useState<{ expertId: string; profile: AdminProfile } | null>(null);
  const [error, setError] = useState<{ expertId: string; message: string } | null>(null);

  useEffect(() => {
    let active = true;
    setLoaded(null);
    setError(null);
    async function load() {
      try {
        const response: { profile: AdminProfile | null } = await api.get(
          `/user/profile/admin/${encodeURIComponent(expertId)}`,
        );
        if (!response.profile) throw new Error("Expert profile unavailable.");
        if (active) setLoaded({ expertId, profile: response.profile });
      } catch (exception) {
        if (active) setError({
          expertId,
          message: exception instanceof Error ? exception.message : "Unable to load expert profile.",
        });
      }
    }
    void load();
    return () => { active = false; };
  }, [expertId]);

  const profile = loaded?.expertId === expertId ? loaded.profile : null;
  const currentError = error?.expertId === expertId ? error.message : null;
  const structured = profile?.structured_profile;
  const axes = structured?.watch_instructions ?? [];
  const criteria = structured?.decision_lenses ?? [];
  const exclusions = structured?.negative_preferences ?? [];
  const editorialText = profile?.profile_editorial_text || profile?.profile_text;

  return (
    <section className="shrink-0 rounded-xl border border-blue-200 bg-blue-50">
      <header className="px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">Expert mandate</h2>
        {expertName && <p className="mt-1 text-xs font-medium text-blue-800">{expertName}</p>}
        <p className="mt-1 text-xs text-gray-500">
          Current profile — it may differ from the profile used to prepare this corpus.
        </p>
      </header>
      <div className="max-h-[35dvh] space-y-3 overflow-y-auto border-t border-blue-100 px-4 py-3">
        {!profile && !currentError && <p className="text-xs text-gray-500">Loading profile…</p>}
        {currentError && <p role="alert" className="text-xs text-red-700">{currentError}</p>}
        {axes.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-900">Monitoring priorities</h3>
            <ul className="mt-2 space-y-2">
              {axes.map((axis, index) => (
                <li key={`${axis.label}-${index}`}>
                  <details className="text-xs text-gray-700">
                    <summary className="cursor-pointer font-medium">
                      {axis.label}{axis.horizon === "FUTURE" ? " · Future" : ""}
                    </summary>
                    <p className="mt-1 whitespace-pre-line leading-5">{axis.instruction}</p>
                  </details>
                </li>
              ))}
            </ul>
          </div>
        )}
        {criteria.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-900">Selection criteria</h3>
            <ul className="mt-2 space-y-2">
              {criteria.map((criterion, index) => (
                <li key={`${criterion.label}-${index}`} className="text-xs leading-5 text-gray-700">
                  <span className="font-medium">{criterion.label}: </span>{criterion.instruction}
                </li>
              ))}
            </ul>
          </div>
        )}
        {profile && (
          <div>
            <h3 className="text-xs font-semibold text-red-800">Exclusions and low-priority contents</h3>
            {exclusions.length > 0 ? (
              <ul className="mt-2 space-y-2">
                {exclusions.map((exclusion, index) => (
                  <li key={index} className="text-xs leading-5 text-gray-700">
                    <p>{exclusion.instruction}</p>
                    {(exclusion.exceptions ?? []).length > 0 && (
                      <p className="mt-1 text-blue-800">
                        Exceptions: {exclusion.exceptions.join("; ")}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-xs text-gray-500">
                No exclusions recorded in the structured profile. Check the editorial profile below.
              </p>
            )}
          </div>
        )}
        {editorialText && (
          <details className="text-xs text-gray-700">
            <summary className="cursor-pointer font-medium">Full editorial profile</summary>
            <p className="mt-2 whitespace-pre-line leading-5">{editorialText}</p>
          </details>
        )}
      </div>
    </section>
  );
}
