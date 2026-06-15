"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

/* ========================================================= */

type Props = {
  userId: string;
};

/* ========================================================= */

export default function UserKeywordsEditor({
  userId,
}: Props) {

  const [keywords, setKeywords] =
    useState<string[]>([]);

  const [newKeyword, setNewKeyword] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res = await api.get(
          `/user/keywords/${userId}`
        );

        setKeywords(
          res?.keywords ?? []
        );

      } catch (e) {

        console.error(
          "❌ keywords load error",
          e
        );

      } finally {

        setLoading(false);

      }
    }

    if (userId) {
      load();
    }

  }, [userId]);

  /* =====================================================
     ADD
  ===================================================== */

  async function addKeyword() {

    const keyword =
      newKeyword.trim();

    if (!keyword) {
      return;
    }

    try {

      setSaving(true);

      await api.post(
        "/user/keywords/add",
        {
          user_id: userId,
          keyword,
        }
      );

      setKeywords((prev) => {

        if (
          prev.some(
            (k) =>
              k.toLowerCase() ===
              keyword.toLowerCase()
          )
        ) {
          return prev;
        }

        return [
          ...prev,
          keyword,
        ];
      });

      setNewKeyword("");

    } catch (e) {

      console.error(
        "❌ add keyword",
        e
      );

      alert(
        "Erreur ajout mot-clé"
      );

    } finally {

      setSaving(false);

    }
  }

  /* =====================================================
     REMOVE
  ===================================================== */

  async function removeKeyword(
    keyword: string
  ) {

    if (
      !confirm(
        `Supprimer "${keyword}" ?`
      )
    ) {
      return;
    }

    try {

      await api.post(
        "/user/keywords/remove",
        {
          user_id: userId,
          keyword,
        }
      );

      setKeywords((prev) =>
        prev.filter(
          (k) => k !== keyword
        )
      );

    } catch (e) {

      console.error(
        "❌ remove keyword",
        e
      );

      alert(
        "Erreur suppression"
      );
    }
  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <div className="
      border
      rounded-lg
      p-6
      space-y-4
    ">

      <div>

        <h2 className="
          text-lg
          font-semibold
        ">
          Mots-clés
        </h2>

        <p className="
          text-sm
          text-gray-500
          mt-1
        ">
          Utilisés pour enrichir
          la sélection des contenus.
        </p>

      </div>

      {/* ADD */}

      <div className="
        flex
        gap-2
      ">

        <input
          type="text"
          value={newKeyword}
          onChange={(e) =>
            setNewKeyword(
              e.target.value
            )
          }
          placeholder="
            premiumization,
            gifting,
            3-tier system...
          "
          className="
            flex-1
            border
            rounded
            px-3
            py-2
          "
          onKeyDown={(e) => {

            if (
              e.key === "Enter"
            ) {

              e.preventDefault();

              addKeyword();
            }
          }}
        />

        <button
          onClick={addKeyword}
          disabled={
            saving ||
            !newKeyword.trim()
          }
          className="
            px-4
            py-2
            rounded
            bg-ratecard-blue
            text-white
            disabled:opacity-50
          "
        >
          Ajouter
        </button>

      </div>

      {/* LIST */}

      {loading ? (

        <div className="
          text-sm
          text-gray-500
        ">
          Chargement...
        </div>

      ) : keywords.length === 0 ? (

        <div className="
          text-sm
          text-gray-500
        ">
          Aucun mot-clé.
        </div>

      ) : (

        <div className="
          flex
          flex-wrap
          gap-2
        ">

          {keywords.map(
            (keyword) => (

            <div
              key={keyword}
              className="
                flex
                items-center
                gap-2
                bg-gray-100
                px-3
                py-1
                rounded-full
              "
            >

              <span>
                {keyword}
              </span>

              <button
                onClick={() =>
                  removeKeyword(
                    keyword
                  )
                }
                className="
                  text-red-500
                  hover:text-red-700
                "
              >
                ×
              </button>

            </div>

          ))}

        </div>

      )}

    </div>
  );
}
