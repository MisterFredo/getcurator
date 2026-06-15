"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

/* ========================================================= */

type Profile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
};

export default function SettingsPage() {

  const [loading, setLoading] =
    useState(true);

  const [savingGeo, setSavingGeo] =
    useState(false);

  const [savingKeyword, setSavingKeyword] =
    useState(false);

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
     KEYWORDS
  ===================================================== */

  async function addKeyword() {

    const value =
      keywordInput.trim();

    if (!value) return;

    try {

      setSavingKeyword(true);

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

    } finally {

      setSavingKeyword(false);

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

      setSavingGeo(true);

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

      alert(
        "Geographies saved"
      );

    } catch (e) {

      console.error(
        "geo save error",
        e
      );

      alert(
        "Error saving geographies"
      );

    } finally {

      setSavingGeo(false);

    }
  }

  /* =====================================================
     LANGUAGE
  ===================================================== */

  async function saveLanguage(
    value: string
  ) {

    try {

      const me =
        await api.get("/user/me");

      const user =
        me?.user;

      if (!user) return;

      await api.post(
        "/user/update",
        {
          user_id:
            user.ID_USER,

          name:
            user.NAME,

          company:
            user.COMPANY,

          role:
            user.ROLE,

          language:
            value,
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
     RENDER
  ===================================================== */

  if (loading) {

    return (
      <div>
        Loading...
      </div>
    );
  }

  return (

    <div className="
      max-w-4xl
      space-y-8
    ">

      <h1 className="
        text-xl
        font-semibold
      ">
        Settings
      </h1>

      {/* =====================================================
          LANGUAGE
      ===================================================== */}

      <div className="
        bg-white
        border
        rounded-xl
        p-6
        space-y-4
      ">

        <h2 className="
          font-semibold
        ">
          Language
        </h2>

        <div className="
          flex
          gap-2
        ">

          <button
            onClick={() =>
              saveLanguage("fr")
            }
            className={`
              px-4 py-2 rounded border
              ${
                language === "fr"
                  ? "bg-emerald-600 text-white"
                  : "bg-white"
              }
            `}
          >
            Français
          </button>

          <button
            onClick={() =>
              saveLanguage("en")
            }
            className={`
              px-4 py-2 rounded border
              ${
                language === "en"
                  ? "bg-emerald-600 text-white"
                  : "bg-white"
              }
            `}
          >
            English
          </button>

        </div>

      </div>

      {/* =====================================================
          KEYWORDS
      ===================================================== */}

      <div className="
        bg-white
        border
        rounded-xl
        p-6
        space-y-4
      ">

        <h2 className="
          font-semibold
        ">
          Keywords
        </h2>

        <div className="
          flex gap-2
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
              rounded
              px-3
              py-2
            "
          />

          <button
            onClick={addKeyword}
            disabled={savingKeyword}
            className="
              px-4
              py-2
              bg-emerald-600
              text-white
              rounded
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

      <div className="
        bg-white
        border
        rounded-xl
        p-6
        space-y-4
      ">

        <h2 className="
          font-semibold
        ">
          Geographies
        </h2>

        <div className="
          grid
          md:grid-cols-3
          gap-4
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
              border
              rounded
              px-3
              py-2
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
              border
              rounded
              px-3
              py-2
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
              border
              rounded
              px-3
              py-2
            "
          />

        </div>

        <button
          onClick={saveGeographies}
          disabled={savingGeo}
          className="
            px-4
            py-2
            bg-emerald-600
            text-white
            rounded
          "
        >
          Save
        </button>

      </div>

    </div>
  );
}
