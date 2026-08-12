"use client";

import {
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";

import UserFavoritesSummary
  from "@/components/settings/UserFavoritesSummary";

import UserExperts
  from "@/components/settings/UserExperts";

/* =========================================================
   TYPES
========================================================= */

type Tab =
  | "expertise"
  | "settings";

type Profile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;
};

type User = {
  NAME?: string | null;
  DISPLAY_NAME?: string | null;
  COMPANY?: string | null;
  LANGUAGE?: string | null;
};

/* =========================================================
   PAGE
========================================================= */

export default function SettingsPage() {

  const [loading, setLoading] =
    useState(true);

  const [activeTab, setActiveTab] =
    useState<Tab>("expertise");

  const [user, setUser] =
    useState<User | null>(
      null,
    );

  const [language, setLanguage] =
    useState("fr");

  const [
    keywordInput,
    setKeywordInput,
  ] = useState("");

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

          api.get(
            "/user/me",
          ),

          api.get(
            "/user/keywords",
          ),

          api.get(
            "/user/profile",
          ),

        ]);

        const currentUser =
          meRes?.user ?? null;

        const profile: Profile =
          profileRes?.profile ?? {};

        setUser(
          currentUser,
        );

        setLanguage(
          currentUser?.LANGUAGE ??
            "fr",
        );

        setKeywords(
          keywordsRes?.keywords ??
            [],
        );

        setProfileText(
          profile.profile_text ??
            "",
        );

      } catch (e) {

        console.error(
          "settings load error",
          e,
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
    value: string,
  ) {

    try {

      await api.post(
        "/user/language",
        {
          language: value,
        },
      );

      setLanguage(value);

    } catch (e) {

      console.error(
        "language update error",
        e,
      );

    }

  }

  /* =====================================================
     KEYWORDS
  ===================================================== */

  async function addKeyword() {

    const value =
      keywordInput.trim();

    if (!value) {
      return;
    }

    try {

      await api.post(
        "/user/keywords/add",
        {
          keyword: value,
        },
      );

      setKeywords(
        previous => [
          ...previous,
          value,
        ],
      );

      setKeywordInput("");

    } catch (e) {

      console.error(
        "keyword add error",
        e,
      );

    }

  }

  /* ===================================================== */

  async function removeKeyword(
    keyword: string,
  ) {

    try {

      await api.post(
        "/user/keywords/remove",
        {
          keyword,
        },
      );

      setKeywords(
        previous =>
          previous.filter(
            item =>
              item !== keyword,
          ),
      );

    } catch (e) {

      console.error(
        "keyword remove error",
        e,
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
        },
      );

      setProfileSaved(true);

      setTimeout(() => {
        setProfileSaved(false);
      }, 2000);

    } catch (e) {

      console.error(
        "profile save error",
        e,
      );

    }

  }

  /* =====================================================
     LOADING
  ===================================================== */

  if (loading) {

    return (
      <div
        className="
          text-sm
          text-gray-500
        "
      >
        Loading...
      </div>
    );

  }

  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div
      className="
        mx-auto
        max-w-6xl
        space-y-6
      "
    >

      {/* =================================================
          HEADER
      ================================================= */}

      <div>

        <h1
          className="
            text-2xl
            font-semibold
            text-gray-900
          "
        >
          Settings
        </h1>

        <div
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Manage your expertise and
          account preferences.
        </div>

      </div>

      {/* =================================================
          TABS
      ================================================= */}

      <div
        className="
          border-b
          border-gray-200
        "
      >

        <div
          className="
            flex
            gap-8
          "
        >

          <button
            type="button"
            onClick={() =>
              setActiveTab(
                "expertise",
              )
            }
            className={`
              border-b-2
              pb-3
              text-sm
              font-medium
              transition

              ${
                activeTab ===
                "expertise"
                  ? `
                    border-emerald-600
                    text-emerald-700
                  `
                  : `
                    border-transparent
                    text-gray-500
                    hover:text-gray-900
                  `
              }
            `}
          >
            My Expertise
          </button>

          <button
            type="button"
            onClick={() =>
              setActiveTab(
                "settings",
              )
            }
            className={`
              border-b-2
              pb-3
              text-sm
              font-medium
              transition

              ${
                activeTab ===
                "settings"
                  ? `
                    border-emerald-600
                    text-emerald-700
                  `
                  : `
                    border-transparent
                    text-gray-500
                    hover:text-gray-900
                  `
              }
            `}
          >
            Preferences
          </button>

        </div>

      </div>

      {/* =================================================
          MY EXPERTISE
      ================================================= */}

      {
        activeTab ===
          "expertise" && (

          <div className="space-y-6">

            {/* =============================================
                IDENTITY
            ============================================= */}

            <div
              className="
                rounded-xl
                border
                bg-white
                p-6
              "
            >

              <div
                className="
                  text-base
                  font-semibold
                  text-gray-900
                "
              >
                Identity
              </div>

              <div
                className="
                  mt-1
                  text-sm
                  text-gray-500
                "
              >
                Your professional identity
                used by GetCurator.
              </div>

              <div
                className="
                  mt-5
                  grid
                  grid-cols-1
                  gap-5
                  md:grid-cols-3
                "
              >

                <div>

                  <div
                    className="
                      text-xs
                      font-medium
                      uppercase
                      tracking-wide
                      text-gray-400
                    "
                  >
                    Name
                  </div>

                  <div
                    className="
                      mt-1
                      text-sm
                      font-medium
                      text-gray-900
                    "
                  >
                    {
                      user?.DISPLAY_NAME ??
                      user?.NAME ??
                      "—"
                    }
                  </div>

                </div>

                <div>

                  <div
                    className="
                      text-xs
                      font-medium
                      uppercase
                      tracking-wide
                      text-gray-400
                    "
                  >
                    Company
                  </div>

                  <div
                    className="
                      mt-1
                      text-sm
                      font-medium
                      text-gray-900
                    "
                  >
                    {
                      user?.COMPANY ??
                      "—"
                    }
                  </div>

                </div>

              </div>

            </div>

            {/* =============================================
                PROFILE + KEYWORDS
            ============================================= */}

            <div
              className="
                grid
                grid-cols-1
                gap-6
                lg:grid-cols-2
              "
            >

              {/* PROFESSIONAL PROFILE */}

              <div
                className="
                  rounded-xl
                  border
                  bg-white
                  p-6
                "
              >

                <div
                  className="
                    text-base
                    font-semibold
                    text-gray-900
                  "
                >
                  Professional Profile
                </div>

                <div
                  className="
                    mt-1
                    text-sm
                    text-gray-500
                  "
                >
                  This profile helps
                  GetCurator understand
                  your role, priorities
                  and strategic context.
                </div>

                <textarea
                  value={
                    profileText
                  }
                  onChange={e =>
                    setProfileText(
                      e.target.value,
                    )
                  }
                  rows={12}
                  className="
                    mt-5
                    w-full
                    rounded-lg
                    border
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
- Retail media monetization`}
                />

                <button
                  type="button"
                  onClick={
                    saveProfile
                  }
                  className="
                    mt-3
                    rounded-lg
                    bg-emerald-600
                    px-4
                    py-2
                    text-sm
                    font-medium
                    text-white
                    hover:bg-emerald-700
                  "
                >
                  {
                    profileSaved
                      ? "✓ Saved"
                      : "Save"
                  }
                </button>

              </div>

              {/* KEYWORDS */}

              <div
                className="
                  rounded-xl
                  border
                  bg-white
                  p-6
                "
              >

                <div
                  className="
                    text-base
                    font-semibold
                    text-gray-900
                  "
                >
                  Keywords
                </div>

                <div
                  className="
                    mt-1
                    text-sm
                    text-gray-500
                  "
                >
                  Add specific topics,
                  companies or concepts
                  you want GetCurator to
                  pay attention to.
                </div>

                <div
                  className="
                    mt-5
                    flex
                    gap-2
                  "
                >

                  <input
                    value={
                      keywordInput
                    }
                    onChange={e =>
                      setKeywordInput(
                        e.target.value,
                      )
                    }
                    onKeyDown={e => {
                      if (
                        e.key ===
                        "Enter"
                      ) {
                        e.preventDefault();
                        addKeyword();
                      }
                    }}
                    placeholder="premiumization"
                    className="
                      min-w-0
                      flex-1
                      rounded-lg
                      border
                      px-3
                      py-2
                      text-sm
                    "
                  />

                  <button
                    type="button"
                    onClick={
                      addKeyword
                    }
                    className="
                      rounded-lg
                      bg-emerald-600
                      px-4
                      text-sm
                      font-medium
                      text-white
                      hover:bg-emerald-700
                    "
                  >
                    Add
                  </button>

                </div>

                <div
                  className="
                    mt-4
                    flex
                    flex-wrap
                    gap-2
                  "
                >

                  {
                    keywords.map(
                      keyword => (

                        <button
                          type="button"
                          key={
                            keyword
                          }
                          onClick={() =>
                            removeKeyword(
                              keyword,
                            )
                          }
                          className="
                            rounded-full
                            bg-gray-100
                            px-3
                            py-1.5
                            text-sm
                            text-gray-700
                            hover:bg-gray-200
                          "
                        >
                          {keyword} ×
                        </button>

                      ),
                    )
                  }

                  {
                    keywords.length ===
                      0 && (

                      <div
                        className="
                          text-sm
                          text-gray-400
                        "
                      >
                        No keywords yet.
                      </div>

                    )
                  }

                </div>

              </div>

            </div>

            {/* =============================================
                FAVORITES
            ============================================= */}

            <div
              className="
                rounded-xl
                border
                bg-white
                p-6
              "
            >
              <UserFavoritesSummary />
            </div>

            {/* =============================================
                EXPERTS
            ============================================= */}

            <div
              className="
                rounded-xl
                border
                bg-white
                p-6
              "
            >
              <UserExperts />
            </div>

          </div>

        )
      }

      {/* =================================================
          ACCOUNT SETTINGS
      ================================================= */}

      {
        activeTab ===
          "settings" && (

          <div
            className="
              rounded-xl
              border
              bg-white
              p-6
            "
          >

            <div
              className="
                text-base
                font-semibold
                text-gray-900
              "
            >
              Language
            </div>

            <div
              className="
                mt-1
                text-sm
                text-gray-500
              "
            >
              Choose the language used
              throughout GetCurator.
            </div>

            <div
              className="
                mt-5
                flex
                gap-2
              "
            >

              <button
                type="button"
                onClick={() =>
                  saveLanguage("fr")
                }
                className={`
                  rounded-full
                  border
                  px-4
                  py-2
                  text-sm
                  font-medium

                  ${
                    language === "fr"
                      ? `
                        border-emerald-600
                        bg-emerald-600
                        text-white
                      `
                      : `
                        bg-white
                        text-gray-700
                        hover:bg-gray-50
                      `
                  }
                `}
              >
                Français
              </button>

              <button
                type="button"
                onClick={() =>
                  saveLanguage("en")
                }
                className={`
                  rounded-full
                  border
                  px-4
                  py-2
                  text-sm
                  font-medium

                  ${
                    language === "en"
                      ? `
                        border-emerald-600
                        bg-emerald-600
                        text-white
                      `
                      : `
                        bg-white
                        text-gray-700
                        hover:bg-gray-50
                      `
                  }
                `}
              >
                English
              </button>

            </div>

          </div>

        )
      }

    </div>

  );

}
