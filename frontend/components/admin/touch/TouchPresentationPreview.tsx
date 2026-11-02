"use client";

import { useMemo, useRef, useState } from "react";
import { buildDocumentHtml } from "@/components/admin/production/ProductionDocumentPreview";
import { buildTouchPresentation, touchExportPeriod } from "@/lib/touch-presentation";
import type { TouchPresentationOptions } from "@/lib/touch-presentation";
import { pdfSubject, productionPdfFilename } from "@/lib/production-export";

export default function TouchPresentationPreview(props: TouchPresentationOptions) {
  const fr = props.outputLanguage !== "en";
  const presentation = useMemo(() => buildTouchPresentation(props), [props.notebook, props.sources,
    props.outputLanguage, props.periodStart, props.periodEnd, props.expertName, props.reportType]);
  const period = touchExportPeriod(props.periodStart, props.periodEnd);
  const filename = productionPdfFilename({ subject: presentation.title, language: fr ? "fr" : "en", ...period })
    ?.replace(/_Report\.pdf$/i, "_Presentation.pdf")
    || `GetCurator_${pdfSubject(presentation.title) || "Touch"}_undated_${fr ? "FR" : "EN"}_Presentation.pdf`;
  const html = useMemo(() => buildDocumentHtml(presentation, filename, fr ? "fr" : "en", true),
    [presentation, filename, fr]);
  const frame = useRef<HTMLIFrameElement>(null);
  const [checked, setChecked] = useState("");
  const [overflow, setOverflow] = useState<number[]>([]);
  const [count, setCount] = useState(0);
  function checkLayout() {
    const sheets = frame.current?.contentDocument?.querySelectorAll<HTMLElement>(".sheet");
    if (!sheets) return;
    const exceeds = (sheet: HTMLElement) => sheet.getBoundingClientRect().height
      > sheet.getBoundingClientRect().width * 210 / 297 + 3 || sheet.scrollWidth > sheet.clientWidth + 2;
    Array.from(sheets).forEach(sheet => {
      sheet.classList.remove("compact");
      if (exceeds(sheet)) sheet.classList.add("compact");
    });
    setOverflow(Array.from(sheets).filter(exceeds).map(sheet => Number(sheet.dataset.page)));
    setCount(sheets.length); setChecked(html);
  }
  function print() {
    const child = frame.current?.contentWindow;
    if (!child || checked !== html) return;
    const previous = window.document.title;
    const restore = () => {
      window.document.title = previous;
      window.removeEventListener("afterprint", restore);
      child.removeEventListener("afterprint", restore);
    };
    window.document.title = filename.replace(/\.pdf$/i, "");
    window.addEventListener("afterprint", restore); child.addEventListener("afterprint", restore);
    try { child.focus(); child.print(); } catch (error) { restore(); throw error; }
  }
  return <section className="space-y-4 rounded-xl border bg-white p-5">
    <div className="touch-output-toolbar space-y-3">
      <h3 className="text-lg font-semibold">{fr ? "Présentation du rapport Touch" : "Touch report presentation"}</h3>
      <p className="text-sm text-slate-600">{fr
        ? "Version sans synthèse LLM : contenu conservé, réparti en pages A4 paysage. Chiffres intégrés aux bullet points, sans section Numbers séparée."
        : "No LLM synthesis: original content arranged across landscape A4 pages. Figures remain within bullet points; no separate Numbers section."}</p>
      <p className="text-xs text-slate-500">{checked === html ? count : presentation.pages.length} {fr ? "pages, bibliographie comprise après contrôle" : "pages, including bibliography after layout check"}</p>
      {checked === html && overflow.length > 0 && <p role="alert" className="rounded bg-amber-50 p-3 text-sm text-amber-900">{fr
        ? `Pages trop denses : ${overflow.join(", ")}. Aucun contenu n’est masqué. Vérifiez l’aperçu d’impression ; ces pages peuvent s’étendre sur plusieurs feuilles.`
        : `Dense pages: ${overflow.join(", ")}. No content is hidden. Check print preview; these pages may span multiple sheets.`}</p>}
      <button type="button" disabled={checked !== html} onClick={print}
        className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
        {fr ? "Imprimer / Enregistrer la présentation en PDF" : "Print / Save presentation as PDF"}
      </button>
      <p className="break-all text-xs text-slate-500">{filename}</p>
      <p className="text-xs text-slate-500">{fr ? "A4 paysage · arrière-plans activés · en-têtes du navigateur désactivés." : "A4 landscape · background graphics on · browser headers and footers off."}</p>
    </div>
    <iframe ref={frame} title={fr ? "Présentation Touch" : "Touch presentation"} srcDoc={html}
      sandbox="allow-same-origin allow-modals" onLoad={checkLayout} className="h-[850px] w-full rounded border" />
  </section>;
}
