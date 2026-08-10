// frontend-curator/components/content/ContentDrawer.tsx

"use client";

import { useEffect, useState } from "react";

import { X } from "lucide-react";

import { useUser } from "@/hooks/useUser";

import { getContent } from "@/lib/watch";

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

    loadContent();

  }, [

    contentId,

  ]);

  async function loadContent() {

    if (!user) {

      return;

    }

    setLoading(
      true,
    );

    try {

      const result =
        await getContent({

          contentId,

          user?.user_id,

        });

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

      {/* ===============================================
          OVERLAY
      =============================================== */}

      <div

        onClick={onClose}

        className="
          fixed
          inset-0
          z-40
          bg-black/40
        "

      />

      {/* ===============================================
          PANEL
      =============================================== */}

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

        {/* ===========================================
            HEADER
        =========================================== */}

        <div
          className="
            sticky
            top-0
            z-10
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

        {/* ===========================================
            CONTENT
        =========================================== */}

        <div
          className="
            p-6
          "
        >

          {loading && (

            <div>

              Loading...

            </div>

          )}

          {!loading &&
            content && (

            <>

              <h1
                className="
                  text-2xl
                  font-semibold
                "
              >

                {content.title}

              </h1>

            </>

          )}

        </div>

      </aside>

    </>

  );

}
