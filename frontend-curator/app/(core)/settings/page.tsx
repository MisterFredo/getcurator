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

type AssistantMessage = {
  role: "user" | "assistant";
  content: string;
};

type AssistantResponse = {
  status: string;
  assistant_version: string;
  action: "ASK" | "PROPOSE";
  message: string;
  proposed_profile_text?: string | null;
  profile_complete: boolean;
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
    savedProfileText,
    setSavedProfileText,
  ] = useState("");

  const [
    profileSaving,
    setProfileSaving,
  ] = useState(false);

  const [
    profileSaved,
    setProfileSaved,
  ] = useState(false);

  const [
    profileError,
    setProfileError,
  ] = useState<string | null>(
    null,
  );

  const [
    assistantOpen,
    setAssistantOpen,
  ] = useState(false);

  const [
    assistantLoading,
    setAssistantLoading,
  ] = useState(false);

  const [
    assistantMessages,
    setAssistantMessages,
  ] = useState<AssistantMessage[]>(
    [],
  );

  const [
    assistantInput,
    setAssistantInput,
  ] = useState("");

  const [
    assistantComplete,
    setAssistantComplete,
  ] = useState(false);

  const [
    assistantError,
    setAssistantError,
  ] = useState<string | null>(
    null,
  );

  const profileHasChanges =
    profileText !== savedProfileText;

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

        const loadedProfileText =
          profile.profile_text || "";

        setLanguage(
          user?.LANGUAGE || "fr",
        );

        setKeywords(
          keywordsRes?.keywords || [],
        );

        setProfileText(
          loadedProfileText,
        );

        setSavedProfileText(
          loadedProfileText,
        );

      } catch (error) {

        console.error(
          "settings load error",
          error,
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

    } catch (error) {

      console.error(
        "language update error",
        error,
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
        current => [
          ...current,
          value,
        ],
      );

      setKeywordInput("");

    } catch (error) {

      console.error(
        "keyword add error",
        error,
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
        current =>
          current.filter(
            item =>
              item !== keyword,
          ),
      );

    } catch (error) {

      console.error(
        "keyword remove error",
        error,
      );

    }

  }

  /* =====================================================
     PROFILE
  ===================================================== */

  async function saveProfile() {

    const cleanedProfile =
      profileText.trim();

    if (!cleanedProfile) {

      setProfileError(
        "Your professional profile cannot be empty.",
      );

      return;

    }

    try {

      setProfileSaving(true);
      setProfileSaved(false);
      setProfileError(null);

      await api.post(
        "/user/profile/update",
        {
          profile_text:
            cleanedProfile,
        },
      );

      setProfileText(
        cleanedProfile,
      );

      setSavedProfileText(
        cleanedProfile,
      );

      setProfileSaved(true);
      setAssistantComplete(false);

      setTimeout(() => {
        setProfileSaved(false);
      }, 2000);

    } catch (error) {

      console.error(
        "profile save error",
        error,
      );

      setProfileError(
        error instanceof Error
          ? error.message
          : "Unable to save your profile.",
      );

    } finally {

      setProfileSaving(false);

    }

  }

  /* =====================================================
     PROFILE ASSISTANT REQUEST
  ===================================================== */

  async function callProfileAssistant(
    messages: AssistantMessage[],
  ) {

    try {

      setAssistantLoading(true);
      setAssistantError(null);

      const response:
        AssistantResponse =
        await api.post(
          "/user/profile/assistant",
          {
            messages,
          },
        );

      const assistantMessage:
        AssistantMessage = {
          role: "assistant",
          content:
            response.message,
        };

      setAssistantMessages([
        ...messages,
        assistantMessage,
      ]);

      if (
        response.action === "PROPOSE"
        && response.proposed_profile_text
      ) {

        setProfileText(
          response.proposed_profile_text,
        );

        setAssistantComplete(true);

      } else {

        setAssistantComplete(false);

      }

    } catch (error) {

      console.error(
        "profile assistant error",
        error,
      );

      setAssistantError(
        error instanceof Error
          ? error.message
          : (
              "The profile assistant "
              + "is currently unavailable."
            ),
      );

    } finally {

      setAssistantLoading(false);

    }

  }

  /* =====================================================
     START PROFILE ASSISTANT
  ===================================================== */

  async function startProfileAssistant() {

    if (profileHasChanges) {

      setAssistantError(
        "Save or discard your current changes before starting the assistant.",
      );

      setAssistantOpen(true);

      return;

    }

    setAssistantOpen(true);
    setAssistantMessages([]);
    setAssistantInput("");
    setAssistantComplete(false);
    setAssistantError(null);

    await callProfileAssistant(
      [],
    );

  }

  /* =====================================================
     SEND ASSISTANT ANSWER
  ===================================================== */

  async function sendAssistantAnswer() {

    const answer =
      assistantInput.trim();

    if (
      !answer
      || assistantLoading
      || assistantComplete
    ) {

      return;

    }

    const messages:
      AssistantMessage[] = [
        ...assistantMessages,
        {
          role: "user",
          content: answer,
        },
      ];

    setAssistantInput("");

    await callProfileAssistant(
      messages,
    );

  }

  /* =====================================================
     CLOSE PROFILE ASSISTANT
  ===================================================== */

  function closeProfileAssistant() {

    setAssistantOpen(false);
    setAssistantMessages([]);
    setAssistantInput("");
    setAssistantComplete(false);
    setAssistantError(null);

  }

  /* =====================================================
     DISCARD PROFILE CHANGES
  ===================================================== */

  function discardProfileChanges() {

    setProfileText(
      savedProfileText,
    );

    setProfileError(null);
    setProfileSaved(false);

    closeProfileAssistant();

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

      {/* =================================================
          EXPERTS
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

        <UserExperts />

      </section>

      {/* =================================================
          FAVORITES + PROFILE
      ================================================= */}

      <div
        className="
          grid
          grid-cols-1
          gap-6
          xl:grid-cols-[1.4fr_0.6fr]
        "
      >

        {/* ===============================================
            FAVORITES
        =============================================== */}

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

        {/* ===============================================
            PROFILE
        =============================================== */}

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

            /* =============================================
                PROFILE SUMMARY
            ============================================= */

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
                          key={keyword}
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
                    || (
                      "No professional "
                      + "profile yet."
                    )}
                </p>

              </div>

            </div>

          ) : (

            /* =============================================
                PROFILE EDITOR
            ============================================= */

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
                    value={keywordInput}
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
                    onClick={addKeyword}
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
                          key={keyword}
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
                    flex
                    flex-wrap
                    items-center
                    justify-between
                    gap-3
                  "
                >

                  <div
                    className="
                      text-sm
                      font-medium
                      text-gray-900
                    "
                  >
                    Professional profile
                  </div>

                  {!assistantOpen && (

                    <button
                      type="button"
                      onClick={
                        startProfileAssistant
                      }
                      className="
                        rounded-lg
                        border
                        border-emerald-200
                        bg-emerald-50
                        px-3
                        py-1.5
                        text-xs
                        font-medium
                        text-emerald-700
                        transition
                        hover:border-emerald-300
                        hover:bg-emerald-100
                      "
                    >
                      Improve with AI
                    </button>

                  )}

                </div>

                <p
                  className="
                    mt-1
                    text-xs
                    leading-5
                    text-gray-500
                  "
                >
                  Describe your responsibilities,
                  priorities, markets and the
                  business questions that matter
                  to you.
                </p>

                <textarea
                  value={profileText}
                  onChange={event => {

                    setProfileText(
                      event.target.value,
                    );

                    setProfileSaved(false);
                    setProfileError(null);

                  }}
                  rows={12}
                  className="
                    mt-3
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
                  placeholder={
                    "Describe your role, "
                    + "expertise, markets and "
                    + "strategic priorities."
                  }
                />

                {profileHasChanges && (

                  <div
                    className="
                      mt-2
                      text-xs
                      text-amber-600
                    "
                  >
                    You have unsaved changes.
                  </div>

                )}

                {profileError && (

                  <div
                    className="
                      mt-3
                      rounded-lg
                      border
                      border-red-200
                      bg-red-50
                      px-3
                      py-2
                      text-xs
                      leading-5
                      text-red-700
                    "
                  >
                    {profileError}
                  </div>

                )}

                <div
                  className="
                    mt-3
                    flex
                    flex-wrap
                    gap-2
                  "
                >

                  <button
                    type="button"
                    onClick={saveProfile}
                    disabled={
                      profileSaving
                      || !profileText.trim()
                      || !profileHasChanges
                    }
                    className="
                      rounded-lg
                      bg-emerald-600
                      px-4
                      py-2
                      text-sm
                      text-white
                      transition
                      hover:bg-emerald-700
                      disabled:cursor-not-allowed
                      disabled:opacity-50
                    "
                  >
                    {profileSaving
                      ? "Saving..."
                      : profileSaved
                        ? "✓ Saved"
                        : "Save profile"}
                  </button>

                  {profileHasChanges && (

                    <button
                      type="button"
                      onClick={
                        discardProfileChanges
                      }
                      disabled={profileSaving}
                      className="
                        rounded-lg
                        border
                        border-gray-200
                        bg-white
                        px-4
                        py-2
                        text-sm
                        text-gray-600
                        transition
                        hover:bg-gray-50
                        disabled:opacity-50
                      "
                    >
                      Discard changes
                    </button>

                  )}

                </div>

              </div>

              {/* PROFILE ASSISTANT */}

              {assistantOpen && (

                <div
                  className="
                    rounded-xl
                    border
                    border-emerald-200
                    bg-emerald-50/50
                    p-4
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

                      <div
                        className="
                          text-sm
                          font-semibold
                          text-gray-900
                        "
                      >
                        Profile assistant
                      </div>

                      <p
                        className="
                          mt-1
                          text-xs
                          leading-5
                          text-gray-500
                        "
                      >
                        Answer a few questions to
                        clarify what GetCurator
                        should monitor for you.
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={
                        closeProfileAssistant
                      }
                      disabled={assistantLoading}
                      className="
                        shrink-0
                        text-xs
                        font-medium
                        text-gray-500
                        hover:text-gray-900
                        disabled:opacity-50
                      "
                    >
                      Close
                    </button>

                  </div>

                  <div
                    className="
                      mt-4
                      max-h-80
                      space-y-3
                      overflow-y-auto
                    "
                  >

                    {assistantMessages.map(
                      (
                        message,
                        index,
                      ) => (

                        <div
                          key={`${message.role}-${index}`}
                          className={`
                            flex

                            ${
                              message.role === "user"
                                ? "justify-end"
                                : "justify-start"
                            }
                          `}
                        >

                          <div
                            className={`
                              max-w-[90%]
                              whitespace-pre-line
                              rounded-xl
                              px-3
                              py-2
                              text-sm
                              leading-5

                              ${
                                message.role === "user"
                                  ? `
                                    bg-emerald-600
                                    text-white
                                  `
                                  : `
                                    border
                                    border-gray-200
                                    bg-white
                                    text-gray-700
                                  `
                              }
                            `}
                          >
                            {message.content}
                          </div>

                        </div>

                      ),
                    )}

                    {assistantLoading && (

                      <div
                        className="
                          flex
                          justify-start
                        "
                      >

                        <div
                          className="
                            rounded-xl
                            border
                            border-gray-200
                            bg-white
                            px-3
                            py-2
                            text-sm
                            text-gray-500
                          "
                        >
                          Preparing the next step...
                        </div>

                      </div>

                    )}

                  </div>

                  {assistantError && (

                    <div
                      className="
                        mt-3
                        rounded-lg
                        border
                        border-red-200
                        bg-red-50
                        px-3
                        py-2
                        text-xs
                        leading-5
                        text-red-700
                      "
                    >
                      {assistantError}
                    </div>

                  )}

                  {assistantComplete ? (

                    <div
                      className="
                        mt-4
                        rounded-lg
                        border
                        border-emerald-200
                        bg-white
                        p-3
                      "
                    >

                      <div
                        className="
                          text-sm
                          font-medium
                          text-emerald-700
                        "
                      >
                        Your profile proposal is ready.
                      </div>

                      <p
                        className="
                          mt-1
                          text-xs
                          leading-5
                          text-gray-500
                        "
                      >
                        It has been copied into the
                        professional profile above.
                        You can edit it before saving.
                        Nothing is saved automatically.
                      </p>

                    </div>

                  ) : (

                    <div
                      className="
                        mt-4
                        flex
                        gap-2
                      "
                    >

                      <textarea
                        value={assistantInput}
                        onChange={event =>
                          setAssistantInput(
                            event.target.value,
                          )
                        }
                        onKeyDown={event => {

                          if (
                            event.key === "Enter"
                            && !event.shiftKey
                          ) {

                            event.preventDefault();

                            sendAssistantAnswer();

                          }

                        }}
                        rows={3}
                        disabled={assistantLoading}
                        placeholder="Type your answer..."
                        className="
                          min-w-0
                          flex-1
                          resize-none
                          rounded-lg
                          border
                          border-gray-200
                          bg-white
                          px-3
                          py-2
                          text-sm
                          leading-5
                          outline-none
                          focus:border-emerald-500
                          disabled:opacity-60
                        "
                      />

                      <button
                        type="button"
                        onClick={
                          sendAssistantAnswer
                        }
                        disabled={
                          assistantLoading
                          || !assistantInput.trim()
                        }
                        className="
                          self-end
                          rounded-lg
                          bg-emerald-600
                          px-4
                          py-2
                          text-sm
                          text-white
                          transition
                          hover:bg-emerald-700
                          disabled:cursor-not-allowed
                          disabled:opacity-50
                        "
                      >
                        Send
                      </button>

                    </div>

                  )}

                </div>

              )}

            </div>

          )}

        </section>

      </div>

    </div>

  );

}
