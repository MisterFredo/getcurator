"use client";

import { useEffect, useState } from "react";

import CardSection from "@/components/ui/CardSection";
import { api } from "@/lib/api";

/* ========================================================= */

type Props = {
  userId: string;
};

/* ========================================================= */

export default function UserKeywordsEditor({
  userId,
}: Props) {

  const [
    keywords,
    setKeywords,
  ] = useState<string[]>([]);

  const [
    newKeyword,
    setNewKeyword,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res =
          await api.get(
            `/user/keywords/${userId}`,
          );

        setKeywords(
          res?.keywords ?? [],
        );

      } catch (error) {

        console.error(
          "Failed to load keywords",
          error,
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
        },
      );

      setKeywords((previous) => {

        if (
          previous.some(
            (item) =>
              item.toLowerCase() ===
              keyword.toLowerCase(),
          )
        ) {
          return previous;
        }

        return [
          ...previous,
          keyword,
        ];

      });

      setNewKeyword("");

    } catch (error) {

      console.error(
        "Failed to add keyword",
        error,
      );

      alert(
        "Unable to add keyword.",
      );

    } finally {

      setSaving(false);

    }

  }

  /* =====================================================
     REMOVE
  ===================================================== */

  async function removeKeyword(
    keyword: string,
  ) {

    if (
      !confirm(
        `Remove "${keyword}"?`,
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
        },
      );

      setKeywords((previous) =>
        previous.filter(
          (item) =>
            item !== keyword,
        ),
      );

    } catch (error) {

      console.error(
        "Failed to remove keyword",
        error,
      );

      alert(
        "Unable to remove keyword.",
      );

    }

  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <CardSection
      title="Keywords"
      description="Additional keywords used to personalize content selection."
    >

      <div className="space-y-6">

        {/* ===================================================== */}
        {/* ADD */}
        {/* ===================================================== */}

        <div className="flex gap-3">

          <input
            type="text"
            value={newKeyword}
            onChange={(e) =>
              setNewKeyword(
                e.target.value,
              )
            }
            placeholder="premiumization, gifting, retail media..."
            className="
              flex-1
              rounded-lg
              border
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
              rounded-lg
              bg-ratecard-blue
              px-5
              py-2
              text-white
              transition
              hover:opacity-90
              disabled:opacity-50
            "
          >

            Add

          </button>

        </div>

        {/* ===================================================== */}
        {/* LIST */}
        {/* ===================================================== */}

        {loading ? (

          <div className="text-sm text-gray-500">
            Loading...
          </div>

        ) : keywords.length === 0 ? (

          <div className="text-sm text-gray-400 italic">
            No keywords defined.
          </div>

        ) : (

          <div className="flex flex-wrap gap-2">

            {keywords.map((keyword) => (

              <div
                key={keyword}
                className="
                  flex
                  items-center
                  gap-2
                  rounded-full
                  bg-gray-100
                  px-3
                  py-1
                "
              >

                <span className="text-sm">
                  {keyword}
                </span>

                <button
                  onClick={() =>
                    removeKeyword(
                      keyword,
                    )
                  }
                  className="
                    text-gray-400
                    transition
                    hover:text-red-600
                  "
                  title="Remove keyword"
                >
                  ×
                </button>

              </div>

            ))}

          </div>

        )}

      </div>

    </CardSection>

  );

}
