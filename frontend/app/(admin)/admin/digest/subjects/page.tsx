"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const endpoint = "/digest/admin/subject-digests";

type Recipient = { id: string; name: string; company?: string };
type SavedDigest = { id: string; name: string; user_id: string; generated_at: string };
type SubjectCard = {
  id: number;
  tier: "MUST" | "NICE";
  title: string;
  development: string;
  reason: string;
  badges?: string[];
  contents: { id: string; title: string }[];
};
type SubjectDigest = {
  id: string;
  profile: { name: string; company?: string; role?: string };
  period_start: string;
  period_end: string;
  executive_brief: string;
  cards: SubjectCard[];
};

function previousMonday() {
  const now = new Date();
  now.setHours(12, 0, 0, 0);
  now.setDate(now.getDate() - ((now.getDay() + 6) % 7) - 7);
  return now.toISOString().slice(0, 10);
}

function message(error: unknown) {
  return error instanceof Error ? error.message : "Action indisponible.";
}

function DigestDocument({ digest }: { digest: SubjectDigest }) {
  return (
    <article className="overflow-hidden rounded-xl border bg-white">
      <header className="space-y-2 bg-ratecard-blue p-7 text-white">
        <p className="text-xs uppercase tracking-wider">
          Weekly User Digest · {digest.period_start} – {digest.period_end}
        </p>
        <h2 className="text-2xl font-semibold">Your Intelligence Briefing by GetCurator</h2>
        <p className="text-sm">{[digest.profile.name, digest.profile.role, digest.profile.company].filter(Boolean).join(" · ")}</p>
      </header>
      <div className="space-y-8 p-7">
        {digest.executive_brief && (
          <section className="rounded-lg bg-slate-50 p-5">
            <h3 className="mb-2 text-lg font-semibold text-ratecard-blue">Your Executive Brief</h3>
            <p className="whitespace-pre-line text-sm leading-relaxed">{digest.executive_brief}</p>
          </section>
        )}
        {!digest.cards.length && <p>Aucun sujet n’atteint le seuil de pertinence.</p>}
        {(["MUST", "NICE"] as const).map(tier => {
          const cards = digest.cards.filter(card => card.tier === tier);
          if (!cards.length) return null;
          return (
            <section key={tier} className="space-y-3">
              <h3 className="text-xl font-semibold text-ratecard-blue">
                {tier === "MUST" ? "Selected for You" : "Also on Your Radar"}
              </h3>
              {cards.map(card => (
                <article key={card.id} className="space-y-3 rounded-lg border p-5">
                  <h4 className="font-semibold">{card.title}</h4>
                  {!!card.badges?.length && (
                    <div className="flex flex-wrap gap-2">
                      {card.badges.map(badge => (
                        <span key={badge} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">{badge}</span>
                      ))}
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{card.development}</p>
                  <p className="border-l-2 border-ratecard-blue pl-3 text-sm leading-relaxed text-slate-700">{card.reason}</p>
                  <details className="text-sm">
                    <summary className="cursor-pointer font-medium text-ratecard-blue">
                      Supporting content ({card.contents.length})
                    </summary>
                    <ul className="mt-2 divide-y">
                      {card.contents.map(content => (
                        <li key={content.id} className="py-2">
                          <a className="text-ratecard-blue underline"
                            href={"https://www.getcurator.ai/feed?analysis_id=" + encodeURIComponent(content.id)}
                            target="_blank" rel="noopener noreferrer">
                            {content.title} ↗
                          </a>
                        </li>
                      ))}
                    </ul>
                  </details>
                </article>
              ))}
            </section>
          );
        })}
      </div>
    </article>
  );
}

export default function SubjectDigestsPage() {
  const [periodStart, setPeriodStart] = useState(previousMonday);
  const [audience, setAudience] = useState<"user" | "expert">("user");
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [selection, setSelection] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [saved, setSaved] = useState<SavedDigest[]>([]);
  const [document, setDocument] = useState<SubjectDigest | null>(null);
  const [progress, setProgress] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    setRecipients([]);
    setSelection([]);
    api.get(endpoint + "/recipients?audience=" + audience)
      .then(result => { if (active) setRecipients(result.recipients); })
      .catch(error => { if (active) setErrors(current => [...current, message(error)]); });
    return () => { active = false; };
  }, [audience]);

  async function readWeek(start: string): Promise<SavedDigest[]> {
    const result = await api.get(endpoint + "?period_start=" + encodeURIComponent(start));
    return result.digests;
  }

  useEffect(() => {
    let active = true;
    setSaved([]);
    setDocument(null);
    if (periodStart) {
      readWeek(periodStart)
        .then(items => { if (active) setSaved(items); })
        .catch(error => { if (active) setErrors(current => [...current, message(error)]); });
    }
    return () => { active = false; };
  }, [periodStart]);

  async function generate(ids: string[], regenerate = false) {
    setErrors([]);
    const failures: string[] = [];
    for (let index = 0; index < ids.length; index += 1) {
      const userId = ids[index];
      const name = recipients.find(item => item.id === userId)?.name ?? document?.profile.name ?? userId;
      setProgress(`${index + 1}/${ids.length} · ${name}`);
      try {
        const result = await api.post(endpoint, { user_id: userId, period_start: periodStart, regenerate });
        setDocument(result.document);
      } catch (error) {
        failures.push(`${name} · ${message(error)}`);
      }
    }
    try {
      setSaved(await readWeek(periodStart));
    } catch (error) {
      failures.push(message(error));
    } finally {
      setErrors(failures);
      setProgress("");
    }
  }

  async function open(id: string) {
    setErrors([]);
    setProgress("Chargement du Digest…");
    try {
      const result = await api.get(endpoint + "/" + encodeURIComponent(id));
      setDocument(result.document);
    } catch (error) {
      setErrors([message(error)]);
    } finally {
      setProgress("");
    }
  }

  const filtered = recipients.filter(person =>
    (person.name + " " + (person.company ?? "")).toLowerCase().includes(search.toLowerCase()));
  const selectedSaved = saved.find(item => item.id === document?.id);

  return (
    <div className="space-y-6">
      <Link href="/admin/digest" className="text-sm text-ratecard-blue underline">Retour aux Digests</Link>
      <h1 className="text-3xl font-semibold">Digests par sujets</h1>
      <fieldset disabled={!!progress} className="space-y-4 rounded-xl border bg-white p-5">
        <div className="flex flex-wrap gap-4">
          <label className="grid gap-1 text-sm">Début de semaine
            <input className="rounded border px-3 py-2" type="date" value={periodStart}
              onChange={event => setPeriodStart(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">Audience
            <select className="rounded border px-3 py-2" value={audience}
              onChange={event => setAudience(event.target.value === "expert" ? "expert" : "user")}>
              <option value="user">Utilisateurs</option>
              <option value="expert">Experts</option>
            </select>
          </label>
        </div>
        <label className="grid gap-1 text-sm">Rechercher un profil
          <input className="rounded border px-3 py-2" value={search} onChange={event => setSearch(event.target.value)} />
        </label>
        <div className="max-h-52 space-y-1 overflow-auto rounded border p-3">
          {filtered.map(person => (
            <label key={person.id} className="flex gap-2 text-sm">
              <input type="checkbox" checked={selection.includes(person.id)} onChange={event => {
                const checked = event.target.checked;
                setSelection(current => checked ? [...current, person.id] : current.filter(id => id !== person.id));
              }} />
              {[person.name, person.company].filter(Boolean).join(" · ")}
            </label>
          ))}
        </div>
        <button type="button" disabled={!periodStart || !selection.length}
          className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"
          onClick={() => void generate(selection)}>
          Générer ({selection.length})
        </button>
      </fieldset>
      {progress && <p role="status">{progress}</p>}
      {!!errors.length && <ul role="alert" className="space-y-1 text-sm text-red-700">
        {errors.map((error, index) => <li key={index}>{error}</li>)}
      </ul>}
      {!!saved.length && (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold">Digests enregistrés cette semaine</h2>
          <div className="flex flex-wrap gap-2">
            {saved.map(item => (
              <button key={item.id} type="button" disabled={!!progress} onClick={() => void open(item.id)}
                className="rounded border bg-white px-3 py-2 text-sm text-ratecard-blue">{item.name}</button>
            ))}
          </div>
        </section>
      )}
      {document && (
        <>
          {selectedSaved && (
            <button type="button" disabled={!!progress} className="rounded border bg-white px-3 py-2 text-sm"
              onClick={() => void generate([selectedSaved.user_id], true)}>Régénérer ce Digest</button>
          )}
          <DigestDocument digest={document} />
        </>
      )}
    </div>
  );
}
