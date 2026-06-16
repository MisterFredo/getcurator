"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import UserFavoritesSummary
from "@/components/settings/UserFavoritesSummary";

/* ========================================================= */

type Profile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
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

  const [geo1, setGeo1] =
    useState("");

  const [geo2, setGeo2] =
    useState("");

  const [geo3, setGeo3] =
    useState("");

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

        setGeo1(
          profile.geography_1 || ""
        );

        setGeo2(
          profile.geography_2 || ""
        );

        setGeo3(
          profile.geography_3 || ""
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
     GEO
  ===================================================== */

  async function saveGeographies() {

    try {

      await api.post(
        "/user/profile/update",
        {
          geography_1:
            geo1 || null,

          geography_2:
            geo2 || null,

          geography_3:
            geo3 || null,
        }
      );

    } catch (e) {

      console.error(
        "geo save error",
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

    <div className="max-w-3xl">

      <h1 className="
        text-xl
        font-semibold
        mb-6
      ">
        Settings
      </h1>

      <div className="
        bg-white
        border
        rounded-xl
        p-6
        space-y-8
      ">

        {/* =====================================================
            LANGUAGE
        ===================================================== */}

        <div>

          <div className="
            text-sm
            font-medium
            mb-3
          ">
            Language
          </div>

          <div className="
            flex
            gap-2
          ">

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

        {/* =====================================================
            KEYWORDS
        ===================================================== */}

        <div>

          <div className="
            text-sm
            font-medium
            mb-3
          ">
            Keywords
          </div>

          <div className="
            flex
            gap-2
            mb-3
          ">

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

          <div className="
            flex
            flex-wrap
            gap-2
          ">

            {keywords.map((keyword) => (

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

            ))}

          </div>

        </div>

        {/* =====================================================
            GEOGRAPHIES
        ===================================================== */}

        <div>

          <div className="
            text-sm
            font-medium
            mb-3
          ">
            Geographies
          </div>

          <div className="
            space-y-2
          ">

            <input
              value={geo1}
              onChange={(e) =>
                setGeo1(
                  e.target.value
                )
              }
              placeholder="Priority 1"
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

            <input
              value={geo2}
              onChange={(e) =>
                setGeo2(
                  e.target.value
                )
              }
              placeholder="Priority 2"
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

            <input
              value={geo3}
              onChange={(e) =>
                setGeo3(
                  e.target.value
                )
              }
              placeholder="Priority 3"
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

          </div>

          <button
            onClick={saveGeographies}
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
            Save
          </button>

        </div>

        <UserFavoritesSummary />

      </div>

    </div>
  );
}
