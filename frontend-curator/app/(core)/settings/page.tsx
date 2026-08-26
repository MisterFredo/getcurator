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

type Profile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;
};

/* =========================================================
   PAGE
========================================================= */

export default function SettingsPage() {

  const [
    profileOpen,
    setProfileOpen,
  ] = useState(false);

  const [loading, setLoading] =
    useState(true);

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

        const user =
          meRes?.user;

        const profile: Profile =
          profileRes?.profile || {};

        setLanguage(
          user?.LANGUAGE || "fr",
        );

        setKeywords(
          keywordsRes?.keywords || [],
        );

        setProfileText(
          profile.profile_text || "",
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

    if (!value) return;

    try {

      await api.post(
        "/user/keywords/add",
        {
          keyword: value,
        },
      );

      setKeywords(
        (prev) => [
          ...prev,
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
        (prev) =>
          prev.filter(
            (k) =>
              k !== keyword,
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
        space-y-6
      "
    >
  
      {/* ===================================================
          EXPERTS
      =================================================== */}
  
      <section
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >
  
        <UserExperts />
  
      </section>
  
      {/* ===================================================
          FAVORITES + PROFILE
      =================================================== */}
  
      <div
        className="
          grid
          grid-cols-1
          gap-6
          xl:grid-cols-[1.4fr_0.6fr]
        "
      >
  
        {/* =================================================
            FAVORITES
        ================================================= */}
  
        <section
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-6
          "
        >
  
          <UserFavoritesSummary />
  
        </section>
  
        {/* =================================================
            PROFILE
        ================================================= */}
  
        <section
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-6
          "
        >
  
          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >
  
            <div>
  
              <h2
                className="
                  text-base
                  font-semibold
                  text-gray-900
                "
              >
                Your profile
              </h2>
  
              <p
                className="
                  mt-1
                  text-xs
                  text-gray-500
                "
              >
                Used to personalize your
                insights and digests.
              </p>
  
            </div>
  
            <button
              type="button"
              onClick={() =>
                setProfileOpen(
                  current => !current,
                )
              }
              className="
                shrink-0
                rounded-lg
                border
                border-gray-200
                px-3
                py-1.5
                text-xs
                font-medium
                text-gray-600
                transition
                hover:border-gray-300
                hover:bg-gray-50
                hover:text-gray-900
              "
            >
              {profileOpen
                ? "Close"
                : "Edit"}
            </button>
  
          </div>
  
          {!profileOpen ? (
  
            /* ===============================================
                PROFILE SUMMARY
            =============================================== */
  
            <div
              className="
                mt-6
                space-y-5
              "
            >
  
              <div>
  
                <div
                  className="
                    mb-2
                    text-[11px]
                    font-medium
                    uppercase
                    tracking-wide
                    text-gray-400
                  "
                >
                  Language
                </div>
  
                <div
                  className="
                    inline-flex
                    rounded-full
                    bg-emerald-50
                    px-3
                    py-1
                    text-xs
                    font-medium
                    uppercase
                    text-emerald-700
                  "
                >
                  {language}
                </div>
  
              </div>
  
              <div>
  
                <div
                  className="
                    mb-2
                    text-[11px]
                    font-medium
                    uppercase
                    tracking-wide
                    text-gray-400
                  "
                >
                  Keywords
                </div>
  
                {keywords.length > 0 ? (
  
                  <div
                    className="
                      flex
                      flex-wrap
                      gap-2
                    "
                  >
  
                    {keywords.map(
                      keyword => (
  
                        <span
                          key={
                            keyword
                          }
                          className="
                            rounded-full
                            bg-gray-100
                            px-3
                            py-1
                            text-xs
                            text-gray-600
                          "
                        >
                          {keyword}
                        </span>
  
                      ),
                    )}
  
                  </div>
  
                ) : (
  
                  <div
                    className="
                      text-sm
                      text-gray-400
                    "
                  >
                    No keywords.
                  </div>
  
                )}
  
              </div>
  
              <div>
  
                <div
                  className="
                    mb-2
                    text-[11px]
                    font-medium
                    uppercase
                    tracking-wide
                    text-gray-400
                  "
                >
                  Professional profile
                </div>
  
                <p
                  className="
                    line-clamp-5
                    whitespace-pre-line
                    text-sm
                    leading-6
                    text-gray-600
                  "
                >
                  {profileText
                    || "No professional profile yet."}
                </p>
  
              </div>
  
            </div>
  
          ) : (
  
            /* ===============================================
                PROFILE EDITOR
            =============================================== */
  
            <div
              className="
                mt-6
                space-y-6
              "
            >
  
              {/* LANGUAGE */}
  
              <div>
  
                <div
                  className="
                    mb-3
                    text-sm
                    font-medium
                    text-gray-900
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
                    type="button"
                    onClick={() =>
                      saveLanguage("fr")
                    }
                    className={`
                      rounded-full
                      border
                      px-3
                      py-1.5
                      text-sm
  
                      ${
  
                        language === "fr"
  
                          ? `
                            border-emerald-600
                            bg-emerald-600
                            text-white
                          `
  
                          : `
                            border-gray-200
                            bg-white
                            hover:bg-gray-50
                          `
  
                      }
                    `}
                  >
                    FR
                  </button>
  
                  <button
                    type="button"
                    onClick={() =>
                      saveLanguage("en")
                    }
                    className={`
                      rounded-full
                      border
                      px-3
                      py-1.5
                      text-sm
  
                      ${
  
                        language === "en"
  
                          ? `
                            border-emerald-600
                            bg-emerald-600
                            text-white
                          `
  
                          : `
                            border-gray-200
                            bg-white
                            hover:bg-gray-50
                          `
  
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
                    mb-3
                    text-sm
                    font-medium
                    text-gray-900
                  "
                >
                  Keywords
                </div>
  
                <div
                  className="
                    flex
                    gap-2
                  "
                >
  
                  <input
                    value={
                      keywordInput
                    }
                    onChange={event =>
                      setKeywordInput(
                        event.target.value,
                      )
                    }
                    onKeyDown={event => {
  
                      if (
                        event.key === "Enter"
                      ) {
  
                        event.preventDefault();
  
                        addKeyword();
  
                      }
  
                    }}
                    placeholder="Add a keyword"
                    className="
                      min-w-0
                      flex-1
                      rounded-lg
                      border
                      border-gray-200
                      px-3
                      py-2
                      text-sm
                      outline-none
                      focus:border-gray-400
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
                      text-white
                    "
                  >
                    Add
                  </button>
  
                </div>
  
                {keywords.length > 0 && (
  
                  <div
                    className="
                      mt-3
                      flex
                      flex-wrap
                      gap-2
                    "
                  >
  
                    {keywords.map(
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
                            py-1
                            text-xs
                            text-gray-600
                            transition
                            hover:bg-gray-200
                          "
                        >
                          {keyword} ×
                        </button>
  
                      ),
                    )}
  
                  </div>
  
                )}
  
              </div>
  
              {/* PROFESSIONAL PROFILE */}
  
              <div>
  
                <div
                  className="
                    mb-3
                    text-sm
                    font-medium
                    text-gray-900
                  "
                >
                  Professional profile
                </div>
  
                <textarea
                  value={
                    profileText
                  }
                  onChange={event =>
                    setProfileText(
                      event.target.value,
                    )
                  }
                  rows={10}
                  className="
                    w-full
                    rounded-lg
                    border
                    border-gray-200
                    p-3
                    text-sm
                    leading-6
                    outline-none
                    focus:border-gray-400
                  "
                  placeholder="
                    Describe your role,
                    expertise and strategic
                    priorities.
                  "
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
                    text-white
                  "
                >
                  {profileSaved
                    ? "✓ Saved"
                    : "Save profile"}
                </button>
  
              </div>
  
            </div>
  
          )}
  
        </section>
  
      </div>
  
    </div>
  
  );
}
