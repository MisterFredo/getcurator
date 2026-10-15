"use client";

import type {
  Production,
  ProductionPagePlan,
} from "@/types/production";

import type {
  TouchNotebookNumber,
} from "@/types/touch";


type Props = {
  production: Production;
  page: ProductionPagePlan;
};


/* =========================================================
   FORMAT VALUES WITHOUT CHANGING SCALE
========================================================= */

function scalar(
  value: string | number | null | undefined,
): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "number") {
    return Number.isFinite(value)
      ? value.toLocaleString(
          "fr-FR",
          {
            maximumFractionDigits: 20,
          },
        )
      : null;
  }

  const text = value.trim();

  return text || null;
}

function numberValue(
  number: TouchNotebookNumber,
): string {
  const value = scalar(number.value);

  if (value !== null) {
    return value;
  }

  const minimum = scalar(
    number.value_min,
  );

  const maximum = scalar(
    number.value_max,
  );

  if (
    minimum !== null &&
    maximum !== null
  ) {
    return `${minimum} – ${maximum}`;
  }

  if (minimum !== null) {
    return `Min. ${minimum}`;
  }

  if (maximum !== null) {
    return `Max. ${maximum}`;
  }

  return "Valeur non renseignée";
}

function metadata(
  value: string | null | undefined,
): string | null {
  const text = value?.trim();

  return text || null;
}


/* =========================================================
   SELECTED NUMBERS
========================================================= */

export default function ProductionPageNumbers({
  production,
  page,
}: Props) {
  const referenceIds = Array.from(
    new Set(
      page.number_reference_ids,
    ),
  );

  if (referenceIds.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3 border-t pt-4">
      <h4 className="text-sm font-semibold text-slate-900">
        Numbers sélectionnés
      </h4>

      <div className="space-y-3">
        {referenceIds.map(
          (referenceId) => {
            const reference =
              production.corpus.evidence_index.find(
                (item) =>
                  item.reference_id ===
                  referenceId,
              );

            const report =
              production.corpus.reports.find(
                (item) =>
                  item.report_id ===
                    reference?.report_id &&
                  item.version_number ===
                    reference?.report_version,
              );

            const number =
              reference?.kind === "NUMBER"
                ? report?.payload.notebook
                    .validated_numbers.find(
                      (item) =>
                        item.number_id ===
                        reference.local_id,
                    )
                : undefined;

            if (!number || !report) {
              return (
                <div
                  key={referenceId}
                  className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800"
                >
                  Number introuvable dans
                  le snapshot du rapport.
                </div>
              );
            }

            const subject =
              report.payload.subject;

            const reportTitle =
              typeof subject === "string" &&
              subject.trim()
                ? subject
                : report.report_id;

            const unit = metadata(
              number.unit,
            );

            const scale = metadata(
              number.scale,
            );

            const zone = metadata(
              number.zone,
            );

            const period = metadata(
              number.period_label,
            );

            const label =
              metadata(number.label) ||
              metadata(number.metric_type) ||
              "Indicateur sans libellé";

            const entities = Array.from(
              new Set(
                number.entities
                  .map(
                    (entity) =>
                      metadata(
                        entity.entity_label,
                      ),
                  )
                  .filter(
                    (
                      item,
                    ): item is string =>
                      item !== null,
                  ),
              ),
            );

            return (
              <article
                key={referenceId}
                className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-4"
              >
                <p className="text-sm font-medium text-slate-900">
                  {label}
                </p>

                <p className="mt-2 break-words text-2xl font-semibold text-emerald-800">
                  {numberValue(number)}
                </p>

                <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
                  <div>
                    <dt className="text-slate-500">
                      Unité
                    </dt>
                    <dd className="mt-1 text-slate-800">
                      {unit || "Non précisée"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">
                      Échelle
                    </dt>
                    <dd className="mt-1 text-slate-800">
                      {scale || "Non précisée"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">
                      Zone
                    </dt>
                    <dd className="mt-1 text-slate-800">
                      {zone || "Non précisée"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">
                      Période de la donnée
                    </dt>
                    <dd className="mt-1 text-slate-800">
                      {period || "Non précisée"}
                    </dd>
                  </div>
                </dl>

                {entities.length > 0 && (
                  <p className="mt-3 text-xs text-slate-600">
                    {entities.join(" · ")}
                  </p>
                )}

                <div className="mt-3 border-t border-emerald-100 pt-3 text-xs text-slate-500">
                  <p>
                    {reportTitle}
                    {" · "}
                    Rapport v
                    {report.version_number}
                  </p>

                  <p className="mt-1 break-all">
                    Number : {number.number_id}
                  </p>
                </div>
              </article>
            );
          },
        )}
      </div>
    </section>
  );
}
