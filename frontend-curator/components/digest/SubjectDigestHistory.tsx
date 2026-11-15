"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge, sourceLink } from "./SubjectDigestDetails";

type Choice = -1 | 0 | 1;
type DigestItem = {
  id: string;
  period_start: string;
  period_end: string;
  card_count: number;
};
type Card = {
  id: number;
  subject_key: string;
  feedback: Choice;
  tier: "MUST" | "NICE";
  title: string;
  development: string;
  reason: string;
  badges?: Badge[];
  contents: { id: string; title: string; source_title?: string; source_url?: string }[];
};
type Document = {
  profile: { name: string; company?: string; role?: string };
  period_start: string;
  period_end: string;
  executive_brief: string;
  cards: Card[];
};

const endpoint = "/digest/subject-digests";

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
  }).format(new Date(value + "T00:00:00Z"));
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function SubjectCard({ card, digestId }: { card: Card; digestId: string }) {
  const [choice, setChoice] = useState(card.feedback);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function vote(next: Choice) {
    setBusy(true);
    setError("");
    try {
      const response = await api.post(endpoint + "/" + encodeURIComponent(digestId) + "/feedback", {
        subject_key: card.subject_key,
        value: choice === next ? 0 : next,
      });
      setChoice(response.feedback);
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="space-y-3 rounded-lg border bg-white p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <h4 className="font-semibold text-slate-900">{card.title}</h4>
        <div className="flex shrink-0 gap-1" role="group" aria-label="Subject relevance">
          <button type="button" disabled={busy} aria-pressed={choice === 1} aria-label="Relevant"
            title="Relevant" onClick={() => void vote(1)}
            className={`rounded border px-2.5 py-1 ${choice === 1 ? "border-emerald-600 bg-emerald-50 text-emerald-700" : "text-slate-600"}`}>
            +
          </button>
          <button type="button" disabled={busy} aria-pressed={choice === -1} aria-label="Not relevant"
            title="Not relevant" onClick={() => void vote(-1)}
            className={`rounded border px-2.5 py-1 ${choice === -1 ? "border-red-600 bg-red-50 text-red-700" : "text-slate-600"}`}>
            −
          </button>
        </div>
      </div>
      {!!card.badges?.length && <div className="flex flex-wrap gap-1.5">
        {card.badges.map((badge, index) => <Badge key={index} badge={badge} />)}
      </div>}
      <p className="text-sm leading-relaxed">{card.development}</p>
      <p className="border-l-2 border-emerald-600 pl-3 text-sm leading-relaxed text-slate-700">
        <strong>Why it matters</strong><br />{card.reason}
      </p>
      <details className="text-sm">
        <summary className="cursor-pointer font-medium text-emerald-700">Supporting content ({card.contents.length})</summary>
        <ul className="mt-2 divide-y">
          {card.contents.map(content => (
            <li key={content.id} className="py-2">
              <Link href={"/feed?analysis_id=" + encodeURIComponent(content.id)}
                target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline">
                {content.title} · Read on GetCurator ↗
              </Link>
              {(content.source_title || sourceLink(content.source_url)) && (
                <div className="text-slate-600">
                  Source: {sourceLink(content.source_url) ? (
                    <a href={sourceLink(content.source_url)} target="_blank" rel="noopener noreferrer"
                      className="underline">{content.source_title || "Original source"} ↗</a>
                  ) : content.source_title}
                </div>
              )}
            </li>
          ))}
        </ul>
      </details>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    </article>
  );
}

function SubjectDigestDrawer({ id, onClose }: { id: string; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [document, setDocument] = useState<Document | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => { element?.close(); };
  }, []);

  useEffect(() => {
    let active = true;
    api.get(endpoint + "/" + encodeURIComponent(id))
      .then(result => { if (active) setDocument(result.document); })
      .catch(failure => { if (active) setError(errorMessage(failure)); });
    return () => { active = false; };
  }, [id]);

  return (
    <dialog ref={dialog} onCancel={event => { event.preventDefault(); onClose(); }}
      aria-label="Digest by topic"
      className="fixed inset-y-0 right-0 left-auto m-0 h-full max-h-none w-full max-w-[900px] bg-white shadow-xl backdrop:bg-black/30">
      <div className="sticky top-0 z-10 flex justify-between border-b bg-white px-5 py-4">
        <span className="font-semibold">Digest by topic</span>
        <button type="button" onClick={onClose} className="rounded border px-3 py-1 text-sm">Close</button>
      </div>
      {error && <p role="alert" className="p-5 text-red-700">{error}</p>}
      {!error && !document && <p role="status" className="p-5">Loading Digest…</p>}
      {document && (
        <>
          <header className="space-y-2 bg-emerald-950 p-6 text-white sm:p-8">
            <p className="text-xs uppercase tracking-wide">{dateLabel(document.period_start)} – {dateLabel(document.period_end)}</p>
            <h2 className="text-2xl font-semibold">Your Intelligence Briefing by GetCurator</h2>
            <p className="text-sm">{[document.profile.name, document.profile.role, document.profile.company].filter(Boolean).join(" · ")}</p>
          </header>
          <div className="space-y-7 p-5 sm:p-8">
            {document.executive_brief && <section className="space-y-2 rounded-lg bg-emerald-50 p-4">
              <h3 className="text-lg font-semibold">Your Executive Brief</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed">{document.executive_brief}</p>
            </section>}
            {!document.cards.length && <p>No topics reached the relevance threshold for this week.</p>}
            {(["MUST", "NICE"] as const).map(tier => {
              const cards = document.cards.filter(card => card.tier === tier);
              return cards.length > 0 && (
                <section key={tier} className="space-y-3">
                  <h3 className="text-lg font-semibold">{tier === "MUST" ? "Selected for You" : "Also on Your Radar"}</h3>
                  {cards.map(card => <SubjectCard key={card.id} card={card} digestId={id} />)}
                </section>
              );
            })}
          </div>
        </>
      )}
    </dialog>
  );
}

export default function SubjectDigestHistory({ query }: { query: string }) {
  const [digests, setDigests] = useState<DigestItem[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.get(endpoint + "/me")
      .then(result => { if (active) setDigests(result.digests); })
      .catch(failure => { if (active) setError(errorMessage(failure)); });
    return () => { active = false; };
  }, []);

  if (query.trim()) return null;
  if (error) return <p role="alert" className="text-sm text-red-700">Digests by topic: {error}</p>;
  if (!digests.length) return null;
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Your Digests by Topic</h2>
      {digests.map(digest => (
        <button key={digest.id} type="button"
          className="flex w-full flex-wrap justify-between gap-2 rounded-lg border bg-white px-4 py-3 text-left text-sm hover:bg-slate-50"
          onClick={() => setActiveId(digest.id)}>
          <span>{dateLabel(digest.period_start)} – {dateLabel(digest.period_end)}</span>
          <span className="font-medium text-emerald-700">{digest.card_count} topics · Open</span>
        </button>
      ))}
      {activeId && <SubjectDigestDrawer key={activeId} id={activeId} onClose={() => setActiveId(null)} />}
    </section>
  );
}
