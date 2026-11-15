"use client";

import { useRef, useState } from "react";
import { Badge, sourceLink } from "./SubjectDigestDetails";

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
  executive_brief: string;
  cards: SubjectCard[];
};

export default function SubjectDigestDocument({ digest }: { digest: SubjectDigest }) {
  const body = useRef<HTMLElement>(null);
  const [copyStatus, setCopyStatus] = useState("");
  const [expanded, setExpanded] = useState(false);

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
        ]) {
          element.style.setProperty(property, styles.getPropertyValue(property));
        }
      });
      clone.querySelectorAll("details").forEach(details => {
        const block = document.createElement("div");
        const heading = document.createElement("p");
        heading.textContent = details.querySelector("summary")?.textContent ?? "Supporting content";
        block.append(heading);
        details.querySelectorAll(":scope > :not(summary)").forEach(node => block.append(node));
        details.replaceWith(block);
      });
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
        <span role="status" className="text-sm text-gray-600">{copyStatus}</span>
      </div>
    <article ref={body} className="overflow-hidden rounded-xl border bg-white">
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
                      {card.badges.map((badge, index) => <Badge key={index} badge={badge} />)}
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{card.development}</p>
                  <p className="border-l-2 border-ratecard-blue pl-3 text-sm leading-relaxed text-slate-700"><strong>Why it matters</strong><br />{card.reason}</p>
                  <details open={expanded || undefined} className="text-sm">
                    <summary className="cursor-pointer font-medium text-ratecard-blue">
                      Supporting content ({card.contents.length})
                    </summary>
                    <ul className="mt-2 divide-y">
                      {card.contents.map(content => (
                        <li key={content.id} className="py-2">
                          <a className="text-ratecard-blue underline"
                            href={"https://www.getcurator.ai/feed?analysis_id=" + encodeURIComponent(content.id)}
                            target="_blank" rel="noopener noreferrer">
                            {content.title} · Read on GetCurator ↗
                          </a>
                          {(content.source_name || content.source_title || sourceLink(content.source_url)) && (
                            <div className="text-sm text-slate-600">
                              Source: {sourceLink(content.source_url) ? (
                                <a href={sourceLink(content.source_url)} target="_blank" rel="noopener noreferrer"
                                  className="underline">{content.source_name || content.source_title || "Original source"} ↗</a>
                              ) : (content.source_name || content.source_title)}
                            </div>
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
