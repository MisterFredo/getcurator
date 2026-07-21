"use client";

import type {
  DigestSection as DigestSectionType,
} from "@/types/digest";

type Props = {
  section: DigestSectionType;
};

export default function DigestSection({
  section,
}: Props) {

  return (

    <section className="rounded-lg border bg-white p-6 space-y-6">

      <div>

        <h2 className="text-xl font-semibold">

          {section.title}

        </h2>

        {section.body && (

          <p className="mt-2 whitespace-pre-wrap text-gray-700">

            {section.body}

          </p>

        )}

      </div>

      {section.cards.length > 0 && (

        <div className="space-y-4">

          {section.cards.map((card) => (

            <a
              key={card.id}
              href={card.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-lg border p-4 hover:bg-gray-50"
            >

              <div className="flex gap-4">

                {card.company_logo && (

                  <img
                    src={card.company_logo}
                    alt=""
                    className="h-12 w-12 rounded object-contain"
                  />

                )}

                <div className="flex-1">

                  <h3 className="font-medium">

                    {card.title}

                  </h3>

                  <p className="mt-1 text-sm text-gray-600">

                    {card.excerpt}

                  </p>

                  <div className="mt-3 text-xs text-gray-400">

                    {card.source_title}

                    {card.published_at && (
                      <>
                        {" • "}
                        {card.published_at}
                      </>
                    )}

                  </div>

                </div>

              </div>

            </a>

          ))}

        </div>

      )}

    </section>

  );

}
