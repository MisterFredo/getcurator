"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Source = { id: string; label: string; quote: string; json_pointer: string };
type Field = { location: string; page_id: string; page_number: number; page_title: string;
  value: string; max_length: number; issues: { code: string; message: string }[]; sources: Source[] };
type Context = { production_id: string; document_artifact_id: string; review_artifact_id: string;
  corpus_sha256: string; context_sha256: string; document_title: string; language: string;
  editable: boolean; unhandled_locations: string[]; fields: Field[] };
type Props = { productionId: string; disabled?: boolean;
  onSavingChange: (value: boolean) => void; onSaved: (productionId: string) => Promise<void> };
const BUTTON = "rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm disabled:opacity-50";
const PRIMARY = "rounded-lg bg-emerald-700 px-4 py-2 text-sm text-white disabled:opacity-50";
const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Impossible de confirmer la correction.";

export default function MonthlyReviewCorrections({ productionId, disabled = false, onSavingChange, onSaved }: Props) {
  const [context, setContext] = useState<Context | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [bindings, setBindings] = useState<Record<string, string[]>>({});
  const [reason, setReason] = useState("Correction des remarques du contrôle qualité.");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const sequence = useRef(0);
  const requestId = useRef<string | null>(null);
  const savingLock = useRef(false);
  useEffect(() => () => { sequence.current += 1; }, []);

  async function load() {
    if (savingLock.current || disabled) return;
    const token = ++sequence.current;
    setLoading(true); setError("");
    try {
      const response: { context: Context } = await api.get(
        `/production/monthly-users/${encodeURIComponent(productionId)}/editorial-context`);
      if (token !== sequence.current) return;
      const next = response.context;
      if (next.production_id !== productionId) throw new Error("Le contexte appartient à un autre rapport.");
      const nextValues: Record<string, string> = {};
      const nextBindings: Record<string, string[]> = {};
      next.fields.forEach(field => { nextValues[field.location] = field.value; nextBindings[field.location] = []; });
      setContext(next); setValues(nextValues); setBindings(nextBindings); requestId.current = null;
    } catch (exception) { if (token === sequence.current) setError(errorMessage(exception)); }
    finally { if (token === sequence.current) setLoading(false); }
  }
  function changeText(location: string, value: string) {
    setValues(current => ({ ...current, [location]: value })); requestId.current = null;
  }
  function toggleSource(location: string, id: string) {
    setBindings(current => {
      const ids = current[location] || [];
      return { ...current, [location]: ids.includes(id) ? ids.filter(value => value !== id) : ids.concat(id) };
    }); requestId.current = null;
  }
  const ready = Boolean(context?.editable && context.fields.length && reason.trim()
    && context.fields.every(field => Boolean(values[field.location]?.trim())
      && values[field.location].trim() !== field.value.trim() && bindings[field.location]?.length));

  async function save() {
    if (!context || !ready || disabled || savingLock.current) return;
    savingLock.current = true; setSaving(true); onSavingChange(true); setError("");
    const token = sequence.current;
    try {
      // Keep the same request ID/body for an unchanged draft after a network error.
      if (!requestId.current) requestId.current = crypto.randomUUID();
      await api.post(`/production/monthly-users/${encodeURIComponent(productionId)}/editorial-edits`, {
        request_id: requestId.current, document_artifact_id: context.document_artifact_id,
        review_artifact_id: context.review_artifact_id, corpus_sha256: context.corpus_sha256,
        context_sha256: context.context_sha256, replacements: values,
        evidence_bindings: bindings, reason: reason.trim(),
      });
      if (token !== sequence.current) return;
      await onSaved(productionId);
    } catch (exception) {
      if (token === sequence.current) setError(`${errorMessage(exception)} Le brouillon est conservé ici. En cas de doute, rouvrez le rapport pour vérifier son historique avant de modifier la demande.`);
    } finally {
      savingLock.current = false;
      if (token === sequence.current) setSaving(false);
      onSavingChange(false);
    }
  }
  function close() {
    if (savingLock.current) return;
    sequence.current += 1; setContext(null); setError(""); requestId.current = null;
  }

  return <section className="space-y-4 rounded-lg border border-slate-200 p-4">
    <div>
      <h3 className="font-semibold text-slate-900">Relecture éditoriale</h3>
      <p className="mt-1 text-sm text-slate-600">Corrigez les passages signalés et sélectionnez leurs preuves. Les autres champs restent conservés. L’enregistrement relance le contrôle qualité, sans valider le rapport directement.</p>
    </div>
    {!context && <button type="button" className={BUTTON} disabled={disabled || loading} onClick={() => void load()}>
      {loading ? "Chargement des passages…" : "Corriger les passages signalés"}
    </button>}
    {error && <p role="alert" className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{error}</p>}
    {context && <>
      <p className="text-sm text-slate-500">{context.document_title} · {context.language.toUpperCase()}</p>
      {!context.editable && <p role="alert" className="text-sm text-amber-800">Ce diagnostic contient des remarques hors édition de texte : {context.unhandled_locations.join(" · ")}. Aucun enregistrement partiel n’est possible.</p>}
      {context.fields.map((field, index) => <div key={field.location} className="space-y-3 rounded-lg bg-slate-50 p-4">
        <h4 className="text-sm font-semibold">Page {field.page_number} · {field.page_title}</h4>
        {field.issues.map((issue, issueIndex) => <p key={issueIndex} className="text-sm text-amber-900">{issue.message}</p>)}
        <details><summary className="cursor-pointer text-xs text-slate-500">Texte enregistré</summary><p className="mt-2 whitespace-pre-wrap text-sm">{field.value}</p></details>
        <label htmlFor={`monthly-correction-${index}`} className="block text-sm font-medium">Texte corrigé ({context.language.toUpperCase()})</label>
        <textarea id={`monthly-correction-${index}`} rows={5} value={values[field.location] || ""}
          maxLength={field.max_length} disabled={saving || disabled || !context.editable}
          onChange={event => changeText(field.location, event.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white p-3 text-sm" />
        <fieldset disabled={saving || disabled || !context.editable} className="space-y-2">
          <legend className="mb-2 text-sm font-medium">Preuves qui soutiennent ce texte</legend>
          {field.sources.map(source => <div key={source.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={(bindings[field.location] || []).includes(source.id)} onChange={() => toggleSource(field.location, source.id)} />
              <span>{source.id} · {source.label}</span>
            </label>
            <details className="ml-6 mt-1"><summary className="cursor-pointer text-xs text-slate-500">Passage cité</summary><blockquote className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{source.quote}</blockquote></details>
          </div>)}
        </fieldset>
      </div>)}
      <label className="block text-sm font-medium">Motif conservé dans l’historique
        <input value={reason} maxLength={2000} disabled={saving || disabled} onChange={event => { setReason(event.target.value); requestId.current = null; }} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
      </label>
      <p className="text-xs text-slate-500">Modifiez chaque passage signalé et sélectionnez au moins une preuve par passage. Les corrections ne sont pas sauvegardées tant que vous n’avez pas enregistré.</p>
      <div className="flex flex-wrap gap-3">
        <button type="button" className={PRIMARY} disabled={!ready || saving || disabled} onClick={() => void save()}>{saving ? "Enregistrement…" : "Enregistrer et relancer les contrôles"}</button>
        <button type="button" className={BUTTON} disabled={saving} onClick={close}>Fermer sans enregistrer</button>
      </div>
    </>}
  </section>;
}
