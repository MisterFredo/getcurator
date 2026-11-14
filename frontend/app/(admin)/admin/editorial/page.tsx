"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  listDailyEditions, readDailyEdition, readDailyJob, refreshDailyJob, startDailyJob,
} from "@/lib/editorial";
import type { DailyJob, Edition, EditionSummary, Topic } from "@/lib/editorial";

const panel = "rounded-xl border border-slate-200 bg-white p-5";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const activeStatuses = new Set(["starting", "queued", "pending", "in_progress", "running"]);
const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Une erreur est survenue.";

function yesterdayInParis() {
  const today = new Intl.DateTimeFormat("fr-CA", { timeZone: "Europe/Paris" }).format(new Date());
  const date = new Date(`${today}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}

export default function EditorialPage() {
  const [date, setDate] = useState("");
  const [job, setJob] = useState<DailyJob>();
  const [history, setHistory] = useState<EditionSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [edition, setEdition] = useState<Edition>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const lock = useRef(false);
  const detailRequest = useRef(0);
  const pendingIds = useRef(new Map<string, string>());
  const active = activeStatuses.has(job?.status.toLowerCase() ?? "");

  useEffect(() => {
    setDate(yesterdayInParis());
    const id = new URLSearchParams(window.location.search).get("job");
    if (id) void readDailyJob(id).then(setJob).catch(err => setError(errorMessage(err)));
  }, []);

  useEffect(() => {
    if (!date) return;
    let stopped = false;
    setHistoryLoading(true);
    void listDailyEditions(date).then(items => {
      if (!stopped) setHistory(items);
    }).catch(err => {
      if (!stopped) setError(errorMessage(err));
    }).finally(() => {
      if (!stopped) setHistoryLoading(false);
    });
    return () => { stopped = true; };
  }, [date, revision]);

  useEffect(() => {
    if (!job?.job_id || !active || busy) return;
    const id = job.job_id;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await refreshDailyJob(id);
        if (stopped) return;
        setJob(next);
        setRevision(value => value + 1);
        if (activeStatuses.has(next.status.toLowerCase())) timer = setTimeout(poll, 8000);
      } catch (err) {
        if (!stopped) setError(errorMessage(err));
      }
    }
    timer = setTimeout(poll, 8000);
    return () => { stopped = true; clearTimeout(timer); };
  }, [job?.job_id, active, busy]);

  async function act(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try { await action(); }
    catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }

  async function generate() {
    const key = `editorial-pending:${date}`;
    let id = pendingIds.current.get(date);
    try { id ??= localStorage.getItem(key) ?? undefined; } catch { /* Storage is optional. */ }
    id ??= crypto.randomUUID();
    pendingIds.current.set(date, id);
    try { localStorage.setItem(key, id); } catch { /* Storage is optional. */ }
    const next = await startDailyJob(date, id);
    pendingIds.current.delete(date);
    try { localStorage.removeItem(key); } catch { /* Storage is optional. */ }
    const url = new URL(window.location.href);
    url.searchParams.set("job", next.job_id);
    window.history.replaceState(null, "", url);
    setJob(next);
    setRevision(value => value + 1);
  }

  async function openEdition(id: string) {
    const token = ++detailRequest.current;
    setEdition(undefined);
    setError("");
    try {
      const item = await readDailyEdition(id);
      if (token === detailRequest.current) setEdition(item);
    } catch (err) {
      if (token === detailRequest.current) setError(errorMessage(err));
    }
  }

  function renderTopic(topic: Topic, rank: number) {
    const articles = new Map(edition?.contents.map(item => [item.id_content, item]));
    return (
      <li key={rank} className="space-y-1 py-3">
        <h4 className="font-semibold">{rank + 1}. {topic.title}</h4>
        <p>{topic.summary}</p>
        {topic.relevance_reason && <p className="text-sm text-slate-600">{topic.relevance_reason}</p>}
        <details className="text-sm">
          <summary className="cursor-pointer">{topic.id_contents.length} contenus associés</summary>
          <ul className="list-disc pl-5">
            {topic.id_contents.map(id => {
              const article = articles.get(id);
              return (
                <li key={id}>
                  <Link
                    href={`/admin/content/edit/${encodeURIComponent(id)}`}
                    className="text-ratecard-blue underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {article?.title || id}
                  </Link>
                  {article?.source_title && (
                    <span className="ml-2 text-slate-600">{article.source_title}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </details>
      </li>
    );
  }

  return (
    <div className="space-y-5 text-slate-900">
      <h1 className="text-2xl font-semibold">Editorial</h1>
      <section className={panel}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="grid gap-1 text-sm">Date de l’édition
            <input type="date" className={button} value={date} disabled={busy} onChange={event => {
              detailRequest.current++;
              setHistory([]);
              setEdition(undefined);
              setDate(event.target.value);
            }} />
          </label>
          <button className="rounded-lg bg-ratecard-blue px-4 py-2 text-sm text-white disabled:opacity-50" disabled={busy || active || !date} onClick={() => void act(generate)}>
            Générer le Quotidien
          </button>
          {job && <button className={button} disabled={busy} onClick={() => void act(async () => {
            setJob(await refreshDailyJob(job.job_id));
            setRevision(value => value + 1);
          })}>Actualiser le suivi</button>}
        </div>
        {error && <p className="mt-3 text-sm text-red-700" role="alert">{error}</p>}
        {job && <div className="mt-4 text-sm">
          <p className="font-semibold">Génération · {job.status}</p>
          <ul>{job.universes.map(item => <li key={item.universe_id}>{item.universe_label} · {item.status}{item.error && ` · ${item.error}`}</li>)}</ul>
        </div>}
      </section>
      <section className={panel}>
        <h2 className="mb-3 font-semibold">Productions quotidiennes</h2>
        {historyLoading && date ? <p>Chargement…</p> : history.length === 0 ? <p>Aucune édition pour cette date.</p> :
          <ul className="space-y-2">{history.map(item => <li key={item.edition_id}>
            <button className={button} onClick={() => void openEdition(item.edition_id)}>{item.universe_label} · {item.content_count} contenus traités</button>
          </li>)}</ul>}
      </section>
      {edition && <>
        <section className={panel}>
          <h2 className="font-semibold">Relevé de pertinence · {edition.universe_label} · {edition.date}</h2>
          <p className="text-sm">{edition.content_count} contenus traités</p>
          <ol className="divide-y">{edition.topics.slice(0, 3).map(renderTopic)}</ol>
          {edition.topics.length > 3 && <details>
            <summary className="cursor-pointer text-sm">Voir les {edition.topics.length - 3} autres sujets</summary>
            <ol className="divide-y">{edition.topics.slice(3).map((topic, index) => renderTopic(topic, index + 3))}</ol>
          </details>}
        </section>
        <section className={panel}>
          <h2 className="font-semibold">Aperçu public</h2>
          {(["a_retenir", "by_the_way"] as const).map(key => <div className="mt-4" key={key}>
            <h3 className="font-semibold">{key === "a_retenir" ? "À retenir" : "By the way"}</h3>
            {edition.preview[key].length === 0 ? <p className="text-sm text-slate-600">Aucun sujet sélectionné.</p> :
              <ul className="space-y-2">{edition.preview[key].map((topic, index) => <li key={index}><strong>{topic.title}</strong><p>{topic.summary}</p></li>)}</ul>}
          </div>)}
        </section>
      </>}
    </div>
  );
}
