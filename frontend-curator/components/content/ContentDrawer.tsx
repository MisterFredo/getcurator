// frontend-curator/components/content/ContentDrawer.tsx

"use client";

import { useEffect, useState } from "react";

import { X } from "lucide-react";

import { useUser } from "@/hooks/useUser";

import {
  getContent,
} from "@/lib/watch";

import ContentHeader from "@/components/content/ContentHeader";
import ContentSummary from "@/components/content/ContentSummary";
import ContentInsights from "@/components/content/ContentInsights";
import ContentNumbers from "@/components/content/ContentNumbers";
import ContentBody from "@/components/content/ContentBody";

import type {
  Content,
} from "@/types/watch";

/* ========================================================= */

type Props = {

  contentId: string;

  onClose: () => void;

};

/* ========================================================= */

export default function ContentDrawer({

  contentId,

  onClose,

}: Props) {

  const {
    user,
  } = useUser();

  const [

    content,

    setContent,

  ] = useState<
    Content | null
  >(null);

  const [

    loading,

    setLoading,

  ] = useState(true);

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    if (!user) {

      return;

    }

    loadContent();

  }, [

    contentId,

    user,

  ]);

  async function loadContent() {

    setLoading(
      true,
    );

    try {

      const result =
        await getContent(

          contentId,

          user.user_id,

        );

      setContent(
        result,
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <>

      {/* =====================================================
          OVERLAY
      ===================================================== */}

      <div

        onClick={onClose}

        className="
          fixed
          inset-0
          z-40
          bg-black/40
        "

      />

      {/* =====================================================
          PANEL
      ===================================================== */}

      <aside
        className="
          fixed
          top-0
          right-0
          z-50
          h-full
          w-[760px]
          max-w-full
          overflow-y-auto
          bg-white
          shadow-2xl
        "
      >

        {/* ===================================================
            HEADER BAR
        =================================================== */}

        <div
          className="
            sticky
            top-0
            z-20
            flex
            items-center
            justify-between
            border-b
            bg-white
            px-6
            py-4
          "
        >

          <h2
            className="
              text-lg
              font-semibold
            "
          >

            Content

          </h2>

          <button
            onClick={onClose}
          >

            <X size={20} />

          </button>

        </div>

        {/* ===================================================
            CONTENT
        =================================================== */}

        <div
          className="
            p-6
            space-y-8
          "
        >

          {loading && (

            <div
              className="
                py-20
                text-center
                text-gray-400
              "
            >

              Loading...

            </div>

          )}

          {!loading &&
            content && (

            <>

              <ContentHeader
                content={content}
              />

              <ContentSummary
                excerpt={
                  content.excerpt
                }
              />

              <ContentInsights

                signal={
                  content.signal_analytique
                }

                mecanique={
                  content.mecanique_expliquee
                }

                enjeu={
                  content.enjeu_strategique
                }

                friction={
                  content.point_de_friction
                }

              />

              <ContentNumbers
                chiffres={
                  content.chiffres
                }
              />

              <ContentBody
                content={
                  content.content_body
                }
              />

            </>

          )}

        </div>

      </aside>

    </>

  );

}
