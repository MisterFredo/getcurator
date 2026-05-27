"use client";

import NewsletterSelector from "@/components/delivery/core/DeliverySelector";

import type {
  NewsletterNewsItem,
} from "@/types/newsletter";

/* =========================================================
   TYPES
========================================================= */

type EditorialItem = {
  id: string;
  type: "news" | "breve";
};

type Props = {
  news: NewsletterNewsItem[];
  breves: NewsletterNewsItem[];

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

  return new Date(date)
    .toLocaleDateString("fr-FR");
}

/* =========================================================
   COMPONENT
========================================================= */

export default function NewsletterSelectors({
  news,
  breves,
  editorialOrder,
  setEditorialOrder,
}: Props) {

  /* =======================================================
     UPDATE SELECTION
  ======================================================= */

  function updateTypeSelection(
    ids: string[],
    type: EditorialItem["type"]
  ) {

    setEditorialOrder((prev) => {

      const prevSameType = prev.filter(
        (i) => i.type === type
      );

      const newItems = ids
        .filter(
          (id) =>
            !prevSameType.some(
              (i) => i.id === id
            )
        )
        .map((id) => ({
          id,
          type,
        }));

      const keptItems = prevSameType.filter(
        (i) => ids.includes(i.id)
      );

      const others = prev.filter(
        (i) => i.type !== type
      );

      return [
        ...others,
        ...keptItems,
        ...newItems,
      ];
    });
  }

  /* =======================================================
     COUNTS
  ======================================================= */

  const newsSelected =
    editorialOrder.filter(
      (i) => i.type === "news"
    ).length;

  const brevesSelected =
    editorialOrder.filter(
      (i) => i.type === "breve"
    ).length;

  /* =======================================================
     UI
  ======================================================= */

  return (

    <div className="space-y-5">

      {/* NEWS */}

      <section className="space-y-2">

        <div className="flex items-center justify-between text-sm">

          <div className="flex items-center gap-2">

            <h2 className="font-semibold tracking-tight">
              News
            </h2>

            <span className="text-xs text-gray-400">
              {news.length} résultats
            </span>

          </div>

          <span className="text-xs font-medium text-gray-500">
            {newsSelected} sélectionnée
            {newsSelected > 1 ? "s" : ""}
          </span>

        </div>

        <NewsletterSelector
          title=""
          items={news.map((n) => ({
            ...n,
            label: `${n.title} · ${formatDate(n.published_at)}`,
          }))}
          selectedIds={
            editorialOrder
              .filter((i) => i.type === "news")
              .map((i) => i.id)
          }
          onChange={(ids) =>
            updateTypeSelection(ids, "news")
          }
          labelKey="label"
        />

      </section>

      {/* BRÈVES */}

      <section className="space-y-2">

        <div className="flex items-center justify-between text-sm">

          <div className="flex items-center gap-2">

            <h2 className="font-semibold tracking-tight">
              Brèves
            </h2>

            <span className="text-xs text-gray-400">
              {breves.length} résultats
            </span>

          </div>

          <span className="text-xs font-medium text-gray-500">
            {brevesSelected} sélectionnée
            {brevesSelected > 1 ? "s" : ""}
          </span>

        </div>

        <NewsletterSelector
          title=""
          items={breves.map((b) => ({
            ...b,
            label: `${b.title} · ${formatDate(b.published_at)}`,
          }))}
          selectedIds={
            editorialOrder
              .filter((i) => i.type === "breve")
              .map((i) => i.id)
          }
          onChange={(ids) =>
            updateTypeSelection(ids, "breve")
          }
          labelKey="label"
        />

      </section>

    </div>
  );
}
