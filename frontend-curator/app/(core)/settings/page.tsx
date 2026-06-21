"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import UserFavoritesSummary from "@/components/settings/UserFavoritesSummary";

/* ========================================================= */

type Profile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;
};

/* ========================================================= */

export default function SettingsPage() {
  const [loading, setLoading] =
    useState(true);

  const [language, setLanguage] =
    useState("fr");

  const [keywordInput, setKeywordInput] =
    useState("");

  const [keywords, setKeywords] =
    useState<string[]>([]);

  const [
    profileText,
    setProfileText,
  ] = useState("");

  const [
    profileSaved,
    setProfileSaved,
  ] = useState(false);

  /* =====================================================
     LOAD
  ===================================================== */

  useEffect(() => {
    async function load() {
      try {
        const [
          meRes,
          keywordsRes,
          profileRes,
        ] = await Promise.all([
          api.get("/user/me"),
          api.get("/user/keywords"),
          api.get("/user/profile"),
        ]);

        const user =
          meRes?.user;

        const profile: Profile =
          profileRes?.profile || {};

        setLanguage(
          user?.LANGUAGE || "fr"
        );

        setKeywords(
          keywordsRes?.keywords || []
        );

        setProfileText(
          profile.profile_text || ""
        );
      } catch (e) {
        console.error(
          "settings load error",
          e
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  /* =====================================================
     LANGUAGE
  ===================================================== */

  async function saveLanguage(
    value: string
  ) {
    try {
      await api.post(
        "/user/language",
        {
          language: value,
        }
      );

      setLanguage(value);
    } catch (e) {
      console.error(
        "language update error",
        e
      );
    }
  }

  /* =====================================================
     KEYWORDS
  ===================================================== */

  async function addKeyword() {
    const value =
      keywordInput.trim();

    if (!value) return;

    try {
      await api.post(
        "/user/keywords/add",
        {
          keyword: value,
        }
      );

      setKeywords((prev) => [
        ...prev,
        value,
      ]);

      setKeywordInput("");
    } catch (e) {
      console.error(
        "keyword add error",
        e
      );
    }
  }

  async function removeKeyword(
    keyword: string
  ) {
    try {
      await api.post(
        "/user/keywords/remove",
        {
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
        "keyword remove error",
        e
      );
    }
  }

  /* =====================================================
     PROFILE
  ===================================================== */

  async function saveProfile() {
    try {
      await api.post(
        "/user/profile/update",
        {
          profile_text:
            profileText || null,
        }
      );

      setProfileSaved(true);

      setTimeout(() => {
        setProfileSaved(false);
      }, 2000);
    } catch (e) {
      console.error(
        "profile save error",
        e
      );
    }
  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {
    return (
      <div className="text-sm text-gray-500">
        Loading...
      </div>
    );
  }

  /* =====================================================
     RENDER
  ===================================================== */

  return (
    <div className="grid grid-cols-[1fr_1fr] gap-6">
      {/* =====================================================
          SETTINGS
      ===================================================== */}

      <div
        className="
          bg-white
          border
          rounded-xl
          p-6
          space-y-8
        "
      >
        {/* LANGUAGE */}

        <div>
          <div
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Language
          </div>

          <div
            className="
              flex
              gap-2
            "
          >
            <button
              onClick={() =>
                saveLanguage("fr")
              }
              className={`
                px-3 py-1.5
                rounded-full
                border
                text-sm
                ${
                  language === "fr"
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-white hover:bg-gray-50"
                }
              `}
            >
              FR
            </button>

            <button
              onClick={() =>
                saveLanguage("en")
              }
              className={`
                px-3 py-1.5
                rounded-full
                border
                text-sm
                ${
                  language === "en"
                    ? "bg-emerald-600 text-white border-emerald-600"
                    : "bg-white hover:bg-gray-50"
                }
              `}
            >
              EN
            </button>
          </div>
        </div>

        {/* KEYWORDS */}

        <div>
          <div
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Keywords
          </div>

          <div
            className="
              flex
              gap-2
              mb-3
            "
          >
            <input
              value={keywordInput}
              onChange={(e) =>
                setKeywordInput(
                  e.target.value
                )
              }
              placeholder="premiumization"
              className="
                flex-1
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

            <button
              onClick={addKeyword}
              className="
                px-4
                rounded-lg
                bg-emerald-600
                text-white
                text-sm
              "
            >
              Add
            </button>
          </div>

          <div
            className="
              flex
              flex-wrap
              gap-2
            "
          >
            {keywords.map(
              (keyword) => (
                <button
                  key={keyword}
                  onClick={() =>
                    removeKeyword(
                      keyword
                    )
                  }
                  className="
                    px-3
                    py-1
                    rounded-full
                    bg-gray-100
                    hover:bg-gray-200
                    text-sm
                  "
                >
                  {keyword} ×
                </button>
              )
            )}
          </div>
        </div>

        {/* PROFESSIONAL PROFILE */}

        <div>
          <div
            className="
              text-sm
              font-medium
              mb-3
            "
          >
            Professional Profile
          </div>

          <div
            className="
              text-sm
              text-gray-500
              mb-3
            "
          >
            This profile is used to generate
            personalized insights and digest
            analysis based on your role,
            expertise and strategic priorities.
          </div>

          <textarea
            value={profileText}
            onChange={(e) =>
              setProfileText(
                e.target.value
              )
            }
            rows={12}
            className="
              w-full
              border
              rounded-lg
              p-3
              text-sm
            "
            placeholder={`Senior Director Retail Media

Focus:
- Commerce Media
- Walmart Connect
- Instacart

Strategic priorities:
- Measurement
- Attribution
- Retail media monetization

Key competitors:
- Amazon
- Walmart
- Kroger`}
          />

          <button
            onClick={saveProfile}
            className="
              mt-3
              px-4
              py-2
              rounded-lg
              bg-emerald-600
              text-white
              text-sm
            "
          >
            {profileSaved
              ? "✓ Saved"
              : "Save"}
          </button>
        </div>
      </div>

      {/* =====================================================
          FAVORITES
      ===================================================== */}

      <div
        className="
          bg-white
          border
          rounded-xl
          p-6
        "
      >
        <UserFavoritesSummary />
      </div>
    </div>
  );
}
