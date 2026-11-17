"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
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
  id: string;
  start: string;
  end: string;
  weeks: number;
  edition_count: number;
  topic_count: number;
  days_without_editions: string[];
  dossiers: Dossier[];
};

type HistoryEntry = { id: string; start: string; end: string; created_at: string; dossier_count: number };
type Comparison = {
  changes: {
    title: string;
    kind: "new" | "updated" | "stable" | "merged";
    status: Dossier["status"];
    previous: { title: string; status: Dossier["status"]; match: string }[];
    added: { id: string; title: string; new_to_window: boolean }[];
    removed_from_dossier: number;
    development: string;
  }[];
  unmatched: {
    title: string;
    status: Dossier["status"];
    match: string;
    still_in_corpus: number;
    outside_current_corpus: number;
  }[];
};

const categories = [
  { id: "ready", label: "Prêts pour analyse" },
  { id: "watch", label: "À suivre" },
  { id: "new", label: "Nouveaux signaux" },
] as const;

const changeLabels = {
  new: "Nouvelle suggestion",
  updated: "Dossier mis à jour",
  stable: "Dossier stable",
  merged: "Regroupement proposé",
};

function statusLabel(status: Dossier["status"]) {
  return { ready: "Prêt pour analyse", watch: "À suivre", new: "Nouveau signal" }[status];
}

function ComparisonPanel({ comparison }: { comparison: Comparison }) {
  return (
    <section className="space-y-3 rounded-lg border bg-white p-4">
      <h2 className="font-semibold">Évolution des dossiers</h2>
      <p className="text-sm text-slate-600">
        Rapprochement automatique par contenus communs et similarité des titres. Les rapprochements par titre seul restent à vérifier.
      </p>
      <ul className="divide-y">
        {comparison.changes.map((item, index) => (
          <li key={index} className="space-y-1 py-3 text-sm">
            <p><strong>{item.title}</strong> · {changeLabels[item.kind]} · {statusLabel(item.status)}</p>
            {!!item.previous.length && <p className="text-slate-600">
              Avant : {item.previous.map(old => old.title + " (" + statusLabel(old.status)
                + (old.match === "title" ? ", titre seulement" : "") + ")").join(" · ")}
            </p>}
            <p>{item.development}</p>
            {!!item.previous.length && <p className="text-xs text-slate-600">
              {item.added.length} contenus rattachés · {item.removed_from_dossier} retirés du dossier
            </p>}
            {!!item.previous.length && !!item.added.length && <details className="text-xs">
              <summary className="cursor-pointer text-ratecard-blue">Voir les contenus rattachés</summary>
              <ul className="mt-1 space-y-1">
                {item.added.map(content => <li key={content.id}>
                  <Link className="underline" href={"/admin/content/edit/" + encodeURIComponent(content.id)}>
                    {content.title || "Ouvrir le contenu"}
                  </Link>
                  {" · "}{content.new_to_window ? "Nouveau dans le corpus" : "Déjà présent dans le corpus"}
                </li>)}
              </ul>
            </details>}
          </li>
        ))}
      </ul>
      {!!comparison.unmatched.length && <>
        <h3 className="font-semibold">Sans correspondance confirmée</h3>
        <ul className="space-y-2 text-sm">
          {comparison.unmatched.map((item, index) => <li key={index}>
            <strong>{item.title}</strong> · {statusLabel(item.status)} · {item.still_in_corpus} contenus encore dans le corpus
            {" · "}{item.outside_current_corpus} absents du corpus actuel
            {item.match === "ambiguous" && " · Plusieurs correspondances possibles"}
          </li>)}
        </ul>
      </>}
    </section>
  );
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
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [previousId, setPreviousId] = useState("");
  const [currentId, setCurrentId] = useState("");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [historyPage, setHistoryPage] = useState(0);

  useEffect(() => {
    let active = true;
    api.get("/editorial/weekly-reviews?limit=50&offset=" + historyPage * 50)
      .then(result => { if (active) setHistory(result.reviews); })
      .catch(error => {
        if (active) setErrors(current => [...current, error instanceof Error ? error.message : "Historique indisponible."]);
      });
    return () => { active = false; };
  }, [historyPage]);

  async function perform(action: () => Promise<void>) {
    setLoading(true);
    setErrors([]);
    setComparison(null);
    try {
      await action();
    } catch (error) {
      setErrors([error instanceof Error ? error.message : "Revue indisponible."]);
    } finally {
      setLoading(false);
    }
  }

  const reviewPath = "/editorial/weekly-reviews";

  async function run() {
    await perform(async () => {
      const review: Review = await api.post(reviewPath, { week_end: weekEnd, available_from: availableFrom });
      setReviews([review]);
      const result = await api.get(reviewPath + "?limit=50");
      setHistoryPage(0);
      setHistory(result.reviews);
      setCurrentId(review.id);
      setPreviousId(result.reviews.find((item: HistoryEntry) => item.end < review.end)?.id ?? "");
    });
  }

  async function open() {
    await perform(async () => {
      const review: Review = await api.get(reviewPath + "/" + encodeURIComponent(currentId));
      setReviews([review]);
    });
  }

  async function compare() {
    await perform(async () => {
      const params = new URLSearchParams({ previous_id: previousId, current_id: currentId });
      const [result, previous, current] = await Promise.all([
        api.get(reviewPath + "/compare?" + params.toString()),
        api.get(reviewPath + "/" + encodeURIComponent(previousId)),
        api.get(reviewPath + "/" + encodeURIComponent(currentId)),
      ]);
      setComparison(result);
      setReviews([previous, current]);
    });
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
        <button type="button" disabled={!weekEnd || !availableFrom} onClick={() => void run()}
          className="rounded bg-ratecard-blue px-4 py-2 text-sm text-white disabled:opacity-50">Lancer et enregistrer la revue</button>
      </fieldset>
      <fieldset disabled={loading} className="space-y-3 rounded-lg border bg-white p-4">
        <legend className="px-2 font-semibold">Historique des revues</legend>
        <div className="flex flex-wrap items-end gap-3">
          {[
            { label: "Revue de référence", value: previousId, change: setPreviousId },
            { label: "Revue à ouvrir ou comparer", value: currentId, change: setCurrentId },
          ].map(field => (
            <label key={field.label} className="grid gap-1 text-sm">
              {field.label}
              <select className="rounded border px-3 py-2" value={field.value} onChange={event => field.change(event.target.value)}>
                <option value="">Choisir une revue</option>
                {history.map(item => <option key={item.id} value={item.id}>
                  {item.end} · {item.dossier_count} dossiers · {item.created_at.slice(0, 19)}
                </option>)}
              </select>
            </label>
          ))}
          <button type="button" disabled={!currentId} onClick={() => void open()}
            className="rounded border px-4 py-2 text-sm disabled:opacity-50">Ouvrir</button>
          <button type="button" disabled={!currentId || !previousId || previousId === currentId} onClick={() => void compare()}
            className="rounded border px-4 py-2 text-sm disabled:opacity-50">Comparer les revues</button>
        </div>
        <div className="flex gap-3 text-xs">
          <button type="button" disabled={!historyPage} onClick={() => setHistoryPage(page => page - 1)}>Page précédente</button>
          <button type="button" disabled={history.length < 50} onClick={() => setHistoryPage(page => page + 1)}>Page suivante</button>
        </div>
      </fieldset>
      {loading && <p role="status" className="text-sm text-slate-600">Revue en cours…</p>}
      {errors.map(error => <p key={error} role="alert" className="text-sm text-red-700">{error}</p>)}
      {comparison && <ComparisonPanel comparison={comparison} />}
      <div className={reviews.length > 1 ? "grid items-start gap-5 xl:grid-cols-2" : "space-y-5"}>
        {reviews.map(review => <ReviewPanel key={review.end} review={review} />)}
      </div>
    </div>
  );
}
