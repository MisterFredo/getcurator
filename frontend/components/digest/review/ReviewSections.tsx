"use client";

import type {
  DigestSection,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  sections: DigestSection[];

};

/* ========================================================= */

export default function ReviewSections({

  sections,

}: Props) {

  return (

    <div className="space-y-10">

      {sections.map((section) => (

        <section
          key={section.id}
          className="space-y-5"
        >

          {/* ============================================= */}
          {/* TITLE */}
          {/* ============================================= */}

          <div>

            <h2 className="text-xl font-semibold">

              {section.title}

            </h2>

          </div>

          {/* ============================================= */}
          {/* BODY */}
          {/* ============================================= */}

          {section.body && (

            <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-700">

              {section.body}

            </div>

          )}

          {/* ============================================= */}
          {/* CARDS */}
          {/* ============================================= */}

          {section.cards.length > 0 && (

            <div className="space-y-4">

              {section.cards.map((card) => (

                <div
                  key={card.id}
                  className="rounded-lg border bg-white p-5"
                >

                  <div className="flex items-start gap-4">

                    {card.company_logo && (

                      <img
                        src={card.company_logo}
                        alt=""
                        className="h-10 w-10 rounded object-contain"
                      />

                    )}

                    <div className="flex-1">

                      <h3 className="font-semibold">

                        {card.title}

                      </h3>

                      <div className="mt-1 text-xs text-gray-500">

                        {card.source_title}

                        {card.published_at && (

                          <>
                            {" • "}
                            {new Date(
                              card.published_at
                            ).toLocaleDateString()}
                          </>

                        )}

                      </div>

                      <p className="mt-3 text-sm text-gray-700">

                        {card.excerpt}

                      </p>

                      {card.url && (

                        <a
                          href={card.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-4 inline-block text-sm font-medium text-ratecard-blue hover:underline"
                        >

                          Open article →

                        </a>

                      )}

                    </div>

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      ))}

    </div>

  );

}
