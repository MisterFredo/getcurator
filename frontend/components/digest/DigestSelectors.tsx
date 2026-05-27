"use client";

import DeliverySelector from "@/components/delivery/DeliverySelector";

import type {
  NewsletterNewsItem,
  NewsletterAnalysisItem,
  NewsletterNumberItem,
} from "@/types/newsletter";

/* =========================================================
   TYPES
========================================================= */

type EditorialItem = {
  id: string;
  type: "news" | "breve" | "analysis" | "number";
};

type Props = {
  news: NewsletterNewsItem[];
  breves: NewsletterNewsItem[];
  analyses: NewsletterAnalysisItem[];
  numbers: NewsletterNumberItem[];

  editorialOrder: EditorialItem[];
  setEditorialOrder: React.Dispatch<
    React.SetStateAction<EditorialItem[]>
  >;
};

/* =========================================================
   HELPERS
========================================================= */

function formatDate(date?: string) {
  if (!date) return "";
  return new Date(date).toLocaleDateString("fr-FR");
}

/* =========================================================
   COMPONENT
========================================================= */

export default function DigestSelectors({
  news,
  breves,
  analyses,
  numbers,
  editorialOrder,
  setEditorialOrder,
}: Props) {

  function updateTypeSelection(
    ids: string[],
    type: EditorialItem["type"]
  ) {
    setEditorialOrder((prev) => {
      const prevSameType = prev.filter(i => i.type === type);

      const newItems = ids
        .filter(id => !prevSameType.some(i => i.id === id))
        .map(id => ({ id, type }));

      const keptItems = prevSameType.filter(i => ids.includes(i.id));

      const others = prev.filter(i => i.type !== type);

      return [...others, ...keptItems, ...newItems];
    });
  }

  const newsSelected = editorialOrder.filter(i => i.type === "news").length;
  const brevesSelected = editorialOrder.filter(i => i.type === "breve").length;
  const analysesSelected = editorialOrder.filter(i => i.type === "analysis").length;
  const numbersSelected = editorialOrder.filter(i => i.type === "number").length;

  return (
    <div className="space-y-5">

      {/* NEWS */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold tracking-tight">News</h2>
            <span className="text-xs text-gray-400">{news.length} résultats</span>
          </div>
          <span className="text-xs font-medium text-gray-500">
            {newsSelected} sélectionnée{newsSelected > 1 ? "s" : ""}
          </span>
        </div>

        <NewsletterSelector
          title=""
          items={news.map(n => ({
            ...n,
            label: `${n.title} · ${formatDate(n.published_at)}`
          }))}
          selectedIds={editorialOrder.filter(i => i.type === "news").map(i => i.id)}
          onChange={(ids) => updateTypeSelection(ids, "news")}
          labelKey="label"
        />
      </section>

      {/* BRÈVES */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold tracking-tight">Brèves</h2>
            <span className="text-xs text-gray-400">{breves.length} résultats</span>
          </div>
          <span className="text-xs font-medium text-gray-500">
            {brevesSelected} sélectionnée{brevesSelected > 1 ? "s" : ""}
          </span>
        </div>

        <DeliverySelector
          title=""
          items={breves.map(b => ({
            ...b,
            label: `${b.title} · ${formatDate(b.published_at)}`
          }))}
          selectedIds={editorialOrder.filter(i => i.type === "breve").map(i => i.id)}
          onChange={(ids) => updateTypeSelection(ids, "breve")}
          labelKey="label"
        />
      </section>

      {/* ANALYSES */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold tracking-tight">Analyses</h2>
            <span className="text-xs text-gray-400">{analyses.length} résultats</span>
          </div>
          <span className="text-xs font-medium text-gray-500">
            {analysesSelected} sélectionnée{analysesSelected > 1 ? "s" : ""}
          </span>
        </div>

        <NewsletterSelector
          title=""
          items={analyses.map(a => ({
            ...a,
            label: `${a.title} · ${formatDate(a.published_at)}`
          }))}
          selectedIds={editorialOrder.filter(i => i.type === "analysis").map(i => i.id)}
          onChange={(ids) => updateTypeSelection(ids, "analysis")}
          labelKey="label"
        />
      </section>

      {/* NUMBERS */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold tracking-tight">Chiffres clés</h2>
            <span className="text-xs text-gray-400">{numbers.length} résultats</span>
          </div>
          <span className="text-xs font-medium text-gray-500">
            {numbersSelected} sélectionné{numbersSelected > 1 ? "s" : ""}
          </span>
        </div>

        <NewsletterSelector
          title=""
          items={numbers.map(n => ({
            ...n,
            label: `${n.label} · ${n.value ?? ""} ${n.unit ?? ""}${n.period ? ` · ${n.period}` : ""}`
          }))}
          selectedIds={editorialOrder.filter(i => i.type === "number").map(i => i.id)}
          onChange={(ids) => updateTypeSelection(ids, "number")}
          labelKey="label"
        />
      </section>

    </div>
  );
}
