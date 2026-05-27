"use client";

import { useEffect, useRef, useState } from "react";
import type { HeaderConfig } from "@/types/newsletter";
import { api } from "@/lib/api";

import HeaderMainFields from "./HeaderMainFields";
import HeaderBranding from "./HeaderBranding";
import EditorialEditor from "./EditorialEditor";

const GCS = process.env.NEXT_PUBLIC_GCS_BASE_URL || "";

type Props = {
  headerConfig: HeaderConfig;
  setHeaderConfig: React.Dispatch<
    React.SetStateAction<HeaderConfig>
  >;

  introText: string;
  setIntroText: (value: string) => void;
};

export default function DigestHeaderConfig({
  headerConfig,
  setHeaderConfig,
  introText,
  setIntroText,
}: Props) {

  const initialized = useRef(false);

  /* 🔥 EVENTS */
  const [events, setEvents] = useState<any[]>([]);

  /* ---------------------------------------------------------
     LOAD EVENTS
  --------------------------------------------------------- */
  useEffect(() => {
    async function loadEvents() {
      try {
        const res = await api.get("/event/list");
        setEvents(res.events || []);
      } catch (e) {
        console.error(e);
      }
    }

    loadEvents();
  }, []);

  /* ---------------------------------------------------------
     DEFAULTS
  --------------------------------------------------------- */
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    setHeaderConfig((prev) => ({
      ...prev,

      variant: prev.variant || "media",

      topBarEnabled:
        prev.topBarEnabled !== undefined
          ? prev.topBarEnabled
          : true,

      topBarColor: prev.topBarColor || "#84CC16",
      periodColor: prev.periodColor || "#84CC16",

      introHtml:
        prev.introHtml ??
        (introText || ""),

      eventId: prev.eventId || undefined,

      heroLink: prev.heroLink || "",
      heroImageUrl: prev.heroImageUrl || "",
      logoLink: prev.logoLink || "",

      title: prev.title || "",
      subtitle: prev.subtitle ?? "",
      period: prev.period ?? "",
    }));
  }, [setHeaderConfig, introText]);

  /* ---------------------------------------------------------
     COMPUTED HERO URL
  --------------------------------------------------------- */
  const heroUrl = headerConfig.eventId
    ? `${GCS}/events/EVENT_${headerConfig.eventId}_rect.jpg`
    : null;

  /* --------------------------------------------------------- */

  return (
    <section className="border border-gray-200 rounded-lg bg-white px-4 py-4 space-y-5">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight">
          Configuration
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3">

        {/* MAIN */}
        <HeaderMainFields
          headerConfig={headerConfig}
          setHeaderConfig={setHeaderConfig}
        />

        {/* BRANDING */}
        <HeaderBranding
          headerConfig={headerConfig}
          setHeaderConfig={setHeaderConfig}
        />

        {/* ===============================
            MEDIA (HEADER)
        =============================== */}
        <div className="col-span-2 border-t pt-3 space-y-3">

          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Media (Header)
          </div>

          {/* 🔥 EVENT SELECT */}
          <select
            className="w-full border rounded px-2 py-1 text-sm"
            value={headerConfig.eventId || ""}
            onChange={(e) => {
              const eventId = e.target.value || undefined;

              const selectedEvent = events.find(
                (ev) => ev.ID_EVENT === eventId
              );

              setHeaderConfig((prev) => ({
                ...prev,
                eventId,

                /* 🔥 AUTO IMAGE */
                heroImageUrl: eventId
                  ? `${GCS}/events/EVENT_${eventId}_rect.jpg`
                  : "",

                /* 🔥 AUTO LINK (le vrai sujet) */
                heroLink:
                  selectedEvent?.EXTERNAL_URL || "",
              }));
            }}
          >
            <option value="">— Aucun event —</option>

            {events.map((e) => (
              <option key={e.ID_EVENT} value={e.ID_EVENT}>
                {e.LABEL}
              </option>
            ))}
          </select>

          {/* 🔥 URL AUTO (READ ONLY) */}
          {heroUrl && (
            <div className="text-xs text-gray-500 break-all">
              {heroUrl}
            </div>
          )}

          {/* 🔥 PREVIEW */}
          {heroUrl && (
            <img
              src={heroUrl}
              className="w-full max-w-md rounded border"
            />
          )}

          {/* 🔽 MANUEL */}
          <input
            type="text"
            placeholder="Lien du visuel (hero)"
            className="w-full border rounded px-2 py-1 text-sm"
            value={headerConfig.heroLink || ""}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                heroLink: e.target.value,
              }))
            }
          />

          <input
            type="text"
            placeholder="URL image (fallback)"
            className="w-full border rounded px-2 py-1 text-sm"
            value={headerConfig.heroImageUrl || ""}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                heroImageUrl: e.target.value,
              }))
            }
          />

          <input
            type="text"
            placeholder="Lien du logo (optionnel)"
            className="w-full border rounded px-2 py-1 text-sm"
            value={headerConfig.logoLink || ""}
            onChange={(e) =>
              setHeaderConfig((prev) => ({
                ...prev,
                logoLink: e.target.value,
              }))
            }
          />

        </div>

        {/* EDITORIAL */}
        <EditorialEditor
          headerConfig={headerConfig}
          setHeaderConfig={setHeaderConfig}
          introText={introText}
          setIntroText={setIntroText}
        />

      </div>
    </section>
  );
}
