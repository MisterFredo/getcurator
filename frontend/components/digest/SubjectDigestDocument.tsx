"use client";

import { useRef, useState } from "react";
import { Badge, sourceLink } from "./SubjectDigestDetails";
import { printSubjectDigest, subjectReportBasename } from "./subjectDigestPrint";

type SubjectCard = {
  id: number;
  tier: "MUST" | "NICE";
  title: string;
  development: string;
  reason: string;
  badges?: Badge[];
  contents: { id: string; title: string; source_name?: string; source_title?: string; source_url?: string }[];
};
export type SubjectDigest = {
  id: string;
  profile: { name: string; company?: string; role?: string };
  period_start: string;
  period_end: string;
  language?: string;
  executive_brief: string;
  cards: SubjectCard[];
};

export default function SubjectDigestDocument({ digest }: { digest: SubjectDigest }) {
  const body = useRef<HTMLElement>(null);
  const [copyStatus, setCopyStatus] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [showPdfName, setShowPdfName] = useState(false);
  const pdfBasename = subjectReportBasename(
    digest.profile.name, digest.period_start, digest.period_end, digest.language,
  );

  async function copyForGmail() {
    if (!body.current) return;
    try {
      const clone = body.current.cloneNode(true) as HTMLElement;
      const originals = body.current.querySelectorAll<HTMLElement>("*");
      clone.querySelectorAll<HTMLElement>("*").forEach((element, index) => {
        const styles = window.getComputedStyle(originals[index]);
        for (const property of [
          "color", "background-color", "font-size", "font-weight", "line-height",
          "text-decoration", "padding", "margin", "border", "border-radius",
          "display", "list-style-type", "letter-spacing",
        ]) {
          element.style.setProperty(property, styles.getPropertyValue(property));
        }
      });
      clone.querySelectorAll("details").forEach(details => {
        const block = document.createElement("div");
        const heading = document.createElement("p");
        heading.textContent = details.querySelector("summary")?.textContent ?? "Supporting content";
        heading.style.cssText = "font-size:12px;font-weight:600;color:#4b6470;margin:14px 0 6px";
        block.style.cssText = "border-top:1px solid #dbe5e8;margin-top:15px";
        block.append(heading);
        details.querySelectorAll(":scope > :not(summary)").forEach(node => block.append(node));
        details.replaceWith(block);
      });
      clone.style.cssText = "font-family:Arial,sans-serif;color:#172530;max-width:680px";
      const html = clone.outerHTML;
      await navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([clone.textContent ?? ""], { type: "text/plain" }),
      })]);
      setCopyStatus("Copié. Colle le Digest dans Gmail.");
    } catch {
      setExpanded(true);
      setCopyStatus("Copie automatique indisponible. Sélectionne le Digest déplié, puis copie-le dans Gmail.");
    }
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="rounded border bg-white px-3 py-2 text-sm" onClick={() => void copyForGmail()}>
          Copier pour Gmail
        </button>
        <button type="button" className="rounded border bg-white px-3 py-2 text-sm text-ratecard-blue" onClick={() => {
          if (!body.current) return;
          setShowPdfName(true);
          printSubjectDigest(body.current, pdfBasename);
        }}>
          Exporter en PDF
        </button>
        <span role="status" className="text-sm text-gray-600">{copyStatus}</span>
        {showPdfName && <p className="w-full break-all text-xs text-gray-600">
          Nom pour Ratecard : <code>{pdfBasename}.pdf</code>
        </p>}
      </div>
    <article ref={body} className="mx-auto max-w-4xl overflow-hidden rounded-xl border bg-white">
      <header className="space-y-2 bg-ratecard-blue p-7 text-white">
        <p className="text-xs uppercase tracking-wider">
          Weekly User Digest · {digest.period_start} – {digest.period_end}
        </p>
        <h2 className="text-2xl font-semibold">Your Intelligence Briefing by GetCurator</h2>
        <p className="text-sm">{[digest.profile.name, digest.profile.role, digest.profile.company].filter(Boolean).join(" · ")}</p>
      </header>
      <div className="space-y-8 p-7">
        {digest.executive_brief && (
          <section data-digest-brief className="rounded-lg bg-slate-50 p-5">
            <h3 className="mb-2 text-lg font-semibold text-ratecard-blue">Your Executive Brief</h3>
            <p className="whitespace-pre-line text-sm leading-relaxed">{digest.executive_brief}</p>
          </section>
        )}
        {!digest.cards.length && <p>Aucun sujet n’atteint le seuil de pertinence.</p>}
        {(["MUST", "NICE"] as const).map(tier => {
          const cards = digest.cards.filter(card => card.tier === tier);
          if (!cards.length) return null;
          return (
            <section key={tier} className="space-y-5">
              <h3 className="border-b border-slate-200 pb-2 text-sm font-semibold uppercase tracking-wider text-ratecard-blue">
                {tier === "MUST" ? "Selected for You" : "Also on Your Radar"}
              </h3>
              {cards.map(card => (
                <article key={card.id} className="space-y-3 rounded-lg border border-slate-200 border-l-4 border-l-ratecard-blue bg-white p-4 sm:p-5">
                  <h4 className="mb-3 text-xl font-bold leading-tight text-ratecard-blue sm:text-2xl">{card.title}</h4>
                  {!!card.badges?.length && (
                    <div data-digest-badges className="flex flex-wrap gap-2">
                      {card.badges.map((badge, index) => <Badge key={index} badge={badge} />)}
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{card.development}</p>
                  <p data-digest-why className="rounded bg-slate-50 px-3 py-2 text-sm leading-relaxed text-slate-700"><strong className="text-ratecard-blue">Why it matters</strong><br />{card.reason}</p>
                  <details open={expanded || undefined} className="border-t border-slate-100 pt-2 text-xs">
                    <summary className="cursor-pointer font-medium text-slate-600">
                      Supporting content ({card.contents.length})
                    </summary>
                    <ul className="mt-1 list-none divide-y divide-slate-100 p-0">
                      {card.contents.map(content => (
                        <li key={content.id} className="py-1.5 text-xs leading-relaxed text-slate-600">
                          <span>{content.title}</span>
                          <br />
                          <a className="text-ratecard-blue underline"
                            href={"https://www.getcurator.ai/feed?analysis_id=" + encodeURIComponent(content.id)}
                            target="_blank" rel="noopener noreferrer">
                            GetCurator ↗
                          </a>
                          {(content.source_name || content.source_title || sourceLink(content.source_url)) && (
                            <span className="text-xs text-slate-600">
                              {" · Source: "}{sourceLink(content.source_url) ? (
                                <a href={sourceLink(content.source_url)} target="_blank" rel="noopener noreferrer"
                                  className="underline">{content.source_name || content.source_title || "Original source"} ↗</a>
                              ) : (content.source_name || content.source_title)}
                            </span>
                          )}
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
    </>
  );
}
