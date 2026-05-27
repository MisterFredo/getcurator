// frontend/components/digest/delivery/DigestPreviewPanel.tsx

"use client";

import DeliveryPreview from "@/components/digest/delivery/DigestPreview";

import type {
  DigestContentItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  editorialHtml?: string;

  contents: DigestContentItem[];
};

/* ========================================================= */

export default function DigestPreviewPanel({
  headerConfig,

  editorialHtml,

  contents,
}: Props) {

  const totalItems =
    contents.length;

  const isEmpty =
    totalItems === 0;

  return (

    <div className="h-full flex flex-col border border-gray-200 rounded-lg bg-white overflow-hidden">

      {/* HEADER */}

      <div className="flex items-center justify-between px-5 py-4 border-b bg-white">

        <h2 className="text-sm font-semibold tracking-tight">
          Preview digest
        </h2>

        <div className="text-xs text-gray-400">
          {totalItems} élément{totalItems > 1 ? "s" : ""}
        </div>

      </div>

      {/* BODY */}

      <div className="flex-1 overflow-y-auto bg-white px-3 py-4">

        {isEmpty ? (

          <div className="h-full flex items-center justify-center text-center text-gray-400 text-sm">

            <div className="space-y-1">

              <div className="font-medium text-gray-500">
                Aucun contenu
              </div>

              <div>
                Sélectionnez un utilisateur.
              </div>

            </div>

          </div>

        ) : (

          <div className="mx-auto w-full max-w-[820px]">

            <DeliveryPreview
              headerConfig={
                headerConfig
              }

              editorialHtml={
                editorialHtml
              }

              contents={
                contents
              }
            />

          </div>

        )}

      </div>

    </div>
  );
}
