import type { TouchCorpusNotebook, TouchContentCandidate } from "@/types/touch";
import type { DocumentPage } from "@/types/production-document";
import type { RenderableDocument } from "@/components/admin/production/ProductionDocumentPreview";

export type TouchPresentationOptions = {
  notebook: TouchCorpusNotebook;
  sources: TouchContentCandidate[];
  outputLanguage?: string;
  periodStart?: string | null;
  periodEnd?: string | null;
  expertName?: string | null;
  reportType?: "MONTHLY" | "RESEARCH";
};
type Block = { text: string; refs: string[]; cautions?: string[] };
const unique = (items: string[]): string[] =>
  Array.from(new Set(items.filter(Boolean)));

// Touch timestamps use an exclusive midnight end; export dates are inclusive.
export function touchExportPeriod(start?: string | null, end?: string | null) {
  const date = (value?: string | null) => {
    if (!value) return null;
    const result = new Date(value);
    return Number.isNaN(result.getTime()) ? null : result;
  };
  const first = date(start), last = date(end);
  if (!first || !last || last < first) return { periodStart: "", periodEnd: "" };
  const exclusive = last > first && last.getUTCHours() === 0 && last.getUTCMinutes() === 0
    && last.getUTCSeconds() === 0 && last.getUTCMilliseconds() === 0;
  return { periodStart: first.toISOString().slice(0, 10),
    periodEnd: new Date(last.getTime() - (exclusive ? 1 : 0)).toISOString().slice(0, 10) };
}

export function buildTouchPresentation(options: TouchPresentationOptions): RenderableDocument {
  const { notebook: n } = options;
  const fr = options.outputLanguage !== "en";
  const sources: RenderableDocument["sources"] = [];
  const pages: DocumentPage[] = [];
  const metadata = new Map(options.sources.map(s => [s.content_id, s]));
  const addReference = (pointer: string, quote: string, contentIds: string[]): string[] => {
    // One reference for each exact notebook passage and cited article.
    // A notebook snapshot has no report ID/version here; neither is fabricated.
    const ids: string[] = [];
    for (const contentId of unique(contentIds)) {
      const source = metadata.get(contentId);
      const id = `S${sources.length + 1}`;
      sources.push({ id, json_pointer: pointer, quote, content_id: contentId,
        label: source ? [source.title, source.source_title, source.published_at?.slice(0, 10)].filter(Boolean).join(" · ") : contentId });
      ids.push(id);
    }
    return ids;
  };
  const page = (layout: DocumentPage["layout"], title: string, blocks: Block[], paragraphs: string[] = []) => {
    pages.push({ page_id: `touch-page-${pages.length + 1}`, layout, title,
      eyebrow: fr ? "Rapport Touch · Présentation" : "Touch report · Presentation",
      paragraphs, bullets: blocks.map(b => b.text + (b.refs.length ? ` [${b.refs.join(", ")}]` : "")),
      metrics: [], chart: null, takeaway: "", cautions: unique(blocks.flatMap(b => b.cautions || [])),
      source_ids: unique(blocks.flatMap(b => b.refs)) });
  };
  const paginate = (layout: DocumentPage["layout"], title: string, blocks: Block[]) => {
    let batch: Block[] = [], weight = 0, index = 0;
    const flush = () => {
      if (!batch.length) return;
      page(layout, title + (index ? (fr ? " — suite" : " — continued") + ` ${index + 1}` : ""), batch);
      index++; batch = []; weight = 0;
    };
    for (const block of blocks) {
      const size = block.text.length + block.refs.join(", ").length + (block.cautions || []).join(" ").length;
      if (batch.length && (batch.length >= 3 || weight + size > 1250)) flush();
      batch.push(block); weight += size;
    }
    flush();
  };
  const title = (options.reportType === "MONTHLY" && options.expertName?.trim()) || n.subject;
  const period = touchExportPeriod(options.periodStart, options.periodEnd);
  const periodLabel = period.periodStart && period.periodEnd
    ? `${period.periodStart} – ${period.periodEnd}` : "";
  page("COVER", title, [], [periodLabel, n.objective].filter(Boolean));

  const summary = (n.executive_summary || []).map((item, i) => ({ text: item.statement,
    refs: addReference(`/notebook/executive_summary/${i}/statement`, item.statement, item.source_content_ids) }));
  paginate("SUMMARY", fr ? "À retenir" : "Key takeaways", summary);
  const noteIndex = new Map(n.notes.map((item, i) => [item.note_id, i]));
  const events = new Map(n.events.map(item => [item.event_id, item]));
  const displayed = new Set<string>();
  const noteBlock = (id: string): Block | null => {
    const i = noteIndex.get(id);
    if (i === undefined || displayed.has(id)) return null;
    displayed.add(id);
    const item = n.notes[i];
    const context = unique([...item.actors, ...item.geographies, ...item.dates]);
    const caution = [item.confidence === "LOW" ? (fr ? "Confiance faible" : "Low confidence") : "",
      item.status !== "VALIDATED" ? item.status : ""].filter(Boolean).join(" · ");
    const refs = addReference(`/notebook/notes/${i}/statement`, item.statement, item.source_content_ids);
    // Preserve the full explanation and context, including all numerical qualifiers.
    return { text: [item.statement, item.explanation, context.length ? `(${context.join(" · ")})` : "",
      caution ? `⚠ ${caution}` : ""].filter(Boolean).join("\n"), refs };
  };
  const collect = (ids: string[]) => ids.map(noteBlock).filter((b): b is Block => b !== null);
  for (const section of n.sections) {
    for (const eventId of section.event_ids) {
      const event = events.get(eventId);
      if (!event) continue;
      const blocks = collect(event.note_ids);
      paginate("CASE_STUDY", `${section.title} — ${event.title}`, blocks);
    }
    paginate("ANALYSIS", section.title, collect(section.note_ids));
  }
  // Old or imperfect saved plans must not silently lose unassigned evidence.
  paginate("ANALYSIS", fr ? "Éléments complémentaires" : "Additional evidence",
    collect(n.notes.filter(item => !displayed.has(item.note_id)).map(item => item.note_id)));
  for (const [i, reading] of Array.from((n.cross_readings || []).entries())) {
    page("ANALYSIS", reading.title, [{ text: `${reading.statement}\n(${reading.reading_type} · ${reading.confidence})`,
      refs: addReference(`/notebook/cross_readings/${i}/statement`, reading.statement, reading.source_content_ids) }]);
  }
  paginate("ANALYSIS", fr ? "Chronologie" : "Timeline", n.timeline.map((item, i) => ({
    text: [item.date, item.label, item.description].filter(Boolean).join(" — "),
    refs: addReference(`/notebook/timeline/${i}/label`, item.label, item.source_content_ids) })));
  paginate("ANALYSIS", fr ? "Divergences entre sources" : "Source discrepancies", n.contradictions.map((item, i) => ({
    text: [item.subject, item.description, item.resolution].filter(Boolean).join("\n"),
    refs: addReference(`/notebook/contradictions/${i}/description`, item.description, item.source_content_ids) })));
  paginate("ANALYSIS", fr ? "Périmètre et limites" : "Scope and limitations", [
    ...n.corpus_strengths.map(text => ({ text: `${fr ? "Point fort" : "Strength"} — ${text}`, refs: [] })),
    ...n.corpus_limits.map(text => ({ text: `${fr ? "Limite" : "Limitation"} — ${text}`, refs: [] })),
  ]);
  // The shared renderer appends the bibliography, using only cited passages.
  return { schema_version: "1.0", template: "GETCURATOR_AUTONOMOUS_V1", title,
    subtitle: periodLabel, pages, sources, review_notes: [fr
      ? "Restitution sans LLM : textes conservés, aucune synthèse nouvelle. Les Numbers séparés ne sont pas affichés. Les références pointent vers le Notebook fourni, sans version de rapport inventée."
      : "No-LLM rendering: original text preserved, no new synthesis. No separate Numbers section. References point to the supplied notebook without an invented report version."] };
}
