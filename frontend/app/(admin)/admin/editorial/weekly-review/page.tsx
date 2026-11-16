"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

type Dossier = {
  title: string;
  status: "ready" | "watch" | "new";
  development: string;
  angle: string;
  evidence: string;
  missing: string;
  content_count: number;
  domain_count: number;
  weeks: { start: string; count: number }[];
  contents: { id: string; title: string; source_url?: string | null }[];
};

type Review = {
  start: string;
  end: string;
  weeks: number;
  edition_count: number;
  topic_count: number;
  days_without_editions: string[];
  dossiers: Dossier[];
};

const categories = [
  { id: "ready", label: "Prêts pour analyse" },
  { id: "watch", label: "À suivre" },
  { id: "new", label: "Nouveaux signaux" },
] as const;

function nextDate(value: string, delta: number) {
  const date = new Date(value + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + delta);
  return date.toISOString().slice(0, 10);
}

function sourceUrl(value?: string | null) {
  try {
    const url = new URL(value ?? "");
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : undefined;
  } catch {
    return undefined;
  }
}

function ReviewPanel({ review }: { review: Review }) {
  return (
    <section className="space-y-5">
      <header className="space-y-1 rounded-lg border bg-slate-50 p-4">
        <h2 className="font-semibold">Revue arrêtée au {review.end}</h2>
        <p className="text-sm text-slate-700">
          {review.start} → {review.end} · {review.weeks}/4 semaines dans la fenêtre · {review.edition_count} Éditos · {review.topic_count} candidats
        </p>
        {!!review.days_without_editions.length && (
          <p className="text-sm text-amber-800">Aucun Édito terminé le : {review.days_without_editions.join(", ")}.</p>
        )}
      </header>
      {!review.dossiers.length && <p className="text-sm text-slate-600">Aucun dossier proposé sur cette période.</p>}
      {categories.map(category => {
        const dossiers = review.dossiers.filter(dossier => dossier.status === category.id);
        if (!dossiers.length) return null;
        return (
          <section key={category.id} className="space-y-3">
            <h3 className="font-semibold">{category.label}</h3>
            {dossiers.map((dossier, index) => (
              <article key={index} className="space-y-2 rounded-lg border bg-white p-4">
                <h4 className="text-lg font-semibold text-ratecard-blue">{dossier.title}</h4>
                <p className="text-xs text-slate-600">
                  {dossier.content_count} contenus distincts · {dossier.domain_count} domaines visibles
                </p>
                <ul className="flex flex-wrap gap-2 text-xs">
                  {dossier.weeks.map(week => (
                    <li key={week.start} className="rounded bg-slate-100 px-2 py-1">
                      Sem. du {week.start} · {week.count}
                    </li>
                  ))}
                </ul>
                <p className="text-sm"><strong>Cette semaine</strong> · {dossier.development}</p>
                {!!dossier.angle && <p className="rounded bg-slate-50 p-2 text-sm"><strong>Angle proposé</strong> · {dossier.angle}</p>}
                {!!dossier.evidence && <p className="text-sm"><strong>Matière disponible</strong> · {dossier.evidence}</p>}
                {!!dossier.missing && <p className="text-sm"><strong>À vérifier</strong> · {dossier.missing}</p>}
                <details className="text-sm">
                  <summary className="cursor-pointer text-ratecard-blue">Voir les contenus associés</summary>
                  <ul className="mt-2 space-y-1">
                    {dossier.contents.map(content => {
                      const url = sourceUrl(content.source_url);
                      return (
                        <li key={content.id}>
                          <Link className="underline" href={"/admin/content/edit/" + encodeURIComponent(content.id)}>
                            {content.title || "Ouvrir le contenu"}
                          </Link>
                          {url && <a className="ml-2 underline" href={url} target="_blank" rel="noopener noreferrer">Source ↗</a>}
                        </li>
                      );
                    })}
                  </ul>
                </details>
              </article>
            ))}
          </section>
        );
      })}
    </section>
  );
}

export default function WeeklyReviewPage() {
  const [weekEnd, setWeekEnd] = useState("2026-11-15");
  const [availableFrom, setAvailableFrom] = useState("2026-10-26");
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  async function run(compare: boolean) {
    setLoading(true);
    setErrors([]);
    const results: Review[] = [];
    const failures: string[] = [];
    try {
      const dates = compare ? [nextDate(weekEnd, -7), weekEnd] : [weekEnd];
      for (const date of dates) {
        try {
          results.push(await api.post("/editorial/weekly-reviews", {
            week_end: date, available_from: availableFrom,
          }));
          setReviews([...results]);
        } catch (failure) {
          failures.push(date + " · " + (failure instanceof Error ? failure.message : "Revue indisponible."));
        }
      }
      setReviews(results);
    } finally {
      setErrors(failures);
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Link href="/admin/editorial" className="text-sm text-ratecard-blue underline">Retour à Editorial</Link>
      <h1 className="text-2xl font-semibold">Sujets à approfondir</h1>
      <fieldset disabled={loading} className="flex flex-wrap items-end gap-4 rounded-lg border bg-white p-4">
        <label className="grid gap-1 text-sm">
          Dimanche de clôture
          <input type="date" value={weekEnd} onChange={e => setWeekEnd(e.target.value)} className="rounded border px-3 py-2" />
        </label>
        <label className="grid gap-1 text-sm">
          Premier lundi couvert
          <input type="date" value={availableFrom} onChange={e => setAvailableFrom(e.target.value)} className="rounded border px-3 py-2" />
        </label>
        <button type="button" disabled={!weekEnd || !availableFrom} onClick={() => void run(false)}
          className="rounded bg-ratecard-blue px-4 py-2 text-sm text-white disabled:opacity-50">Lancer la revue</button>
        <button type="button" disabled={!weekEnd || !availableFrom} onClick={() => void run(true)}
          className="rounded border px-4 py-2 text-sm disabled:opacity-50">Comparer avec la semaine précédente</button>
      </fieldset>
      {loading && <p role="status" className="text-sm text-slate-600">Revue en cours…</p>}
      {errors.map(error => <p key={error} role="alert" className="text-sm text-red-700">{error}</p>)}
      <div className={reviews.length > 1 ? "grid items-start gap-5 xl:grid-cols-2" : "space-y-5"}>
        {reviews.map(review => <ReviewPanel key={review.end} review={review} />)}
      </div>
    </div>
  );
}
