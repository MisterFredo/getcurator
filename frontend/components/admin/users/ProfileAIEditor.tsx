"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import CardSection from "@/components/ui/CardSection";
import { api } from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  userId: string;
};

type StructuredProfile = Record<
  string,
  unknown
>;

type UserProfile = {
  geography_1?: string | null;
  geography_2?: string | null;
  geography_3?: string | null;
  profile_text?: string | null;

  structured_profile?:
    | StructuredProfile
    | null;

  profile_structured_status?:
    | string
    | null;

  profile_structured_error?:
    | string
    | null;

  profile_structured_at?:
    | string
    | null;

  profile_schema_version?:
    | string
    | null;

  profile_transformer_version?:
    | string
    | null;
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

  proposed_profile_text?:
    | string
    | null;

  profile_complete: boolean;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function ProfileAIEditor({
  userId,
}: Props) {

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [
    regenerating,
    setRegenerating,
  ] = useState(false);

  const [
    profileText,
    setProfileText,
  ] = useState("");

  const [
    savedProfileText,
    setSavedProfileText,
  ] = useState("");

  const [
    structuredProfile,
    setStructuredProfile,
  ] = useState<
    StructuredProfile | null
  >(null);

  const [
    structuredStatus,
    setStructuredStatus,
  ] = useState<
    string | null
  >(null);

  const [
    structuredError,
    setStructuredError,
  ] = useState<
    string | null
  >(null);

  const [
    structuredAt,
    setStructuredAt,
  ] = useState<
    string | null
  >(null);

  const [
    schemaVersion,
    setSchemaVersion,
  ] = useState<
    string | null
  >(null);

  const [
    transformerVersion,
    setTransformerVersion,
  ] = useState<
    string | null
  >(null);

  const [
    assistantOpen,
    setAssistantOpen,
  ] = useState(false);

  const [
    assistantLoading,
    setAssistantLoading,
  ] = useState(false);

  const [
    assistantInput,
    setAssistantInput,
  ] = useState("");

  const [
    assistantMessages,
    setAssistantMessages,
  ] = useState<
    AssistantMessage[]
  >([]);

  const [
    assistantError,
    setAssistantError,
  ] = useState<
    string | null
  >(null);

  const [
    proposalReady,
    setProposalReady,
  ] = useState(false);

  const hasUnsavedChanges = (
    profileText !== savedProfileText
  );

  /* =====================================================
     LOAD PROFILE
  ===================================================== */

  const loadProfile = useCallback(
    async () => {

      if (!userId) return;

      try {

        setLoading(true);

        const response = await api.get(
          `/user/profile/${userId}`,
        );

        const profile: UserProfile = (
          response?.profile
          ?? {}
        );

        const nextProfileText = (
          profile.profile_text
          ?? ""
        );

        setProfileText(
          nextProfileText
        );

        setSavedProfileText(
          nextProfileText
        );

        setStructuredProfile(
          profile.structured_profile
          ?? null
        );

        setStructuredStatus(
          profile.profile_structured_status
          ?? null
        );

        setStructuredError(
          profile.profile_structured_error
          ?? null
        );

        setStructuredAt(
          profile.profile_structured_at
          ?? null
        );

        setSchemaVersion(
          profile.profile_schema_version
          ?? null
        );

        setTransformerVersion(
          profile.profile_transformer_version
          ?? null
        );

      } catch (error) {

        console.error(
          "Failed to load profile",
          error,
        );

      } finally {

        setLoading(false);

      }

    },
    [
      userId,
    ],
  );

  useEffect(() => {

    setAssistantOpen(false);
    setAssistantMessages([]);
    setAssistantInput("");
    setAssistantError(null);
    setProposalReady(false);

    loadProfile();

  }, [
    loadProfile,
  ]);

  /* =====================================================
     SAVE PROFILE
  ===================================================== */

  async function saveProfile() {

    const cleanedProfile = (
      profileText.trim()
    );

    if (!cleanedProfile) {

      alert(
        "The profile cannot be empty.",
      );

      return;

    }

    try {

      setSaving(true);

      await api.post(
        "/user/profile/update",
        {
          user_id: userId,
          profile_text: cleanedProfile,
        },
      );

      await loadProfile();

      setProposalReady(false);

      alert(
        "Profile and structured profile updated.",
      );

    } catch (error) {

      console.error(
        "Failed to save profile",
        error,
      );

      alert(
        "Unable to save the profile.",
      );

    } finally {

      setSaving(false);

    }

  }

  /* =====================================================
     REGENERATE STRUCTURED PROFILE
  ===================================================== */

  async function regenerateProfile() {

    if (!savedProfileText.trim()) {

      alert(
        "Save a profile before regenerating it.",
      );

      return;

    }

    if (hasUnsavedChanges) {

      alert(
        "Save the current changes before regenerating.",
      );

      return;

    }

    try {

      setRegenerating(true);

      await api.post(
        "/user/profile/regenerate",
        {
          user_id: userId,
        },
      );

      await loadProfile();

      alert(
        "Structured profile regenerated.",
      );

    } catch (error) {

      console.error(
        "Failed to regenerate profile",
        error,
      );

      alert(
        "Unable to regenerate the structured profile.",
      );

    } finally {

      setRegenerating(false);

    }

  }

  /* =====================================================
     CALL PROFILE ASSISTANT
  ===================================================== */

  async function callProfileAssistant(
    messages: AssistantMessage[],
  ) {

    try {

      setAssistantLoading(true);
      setAssistantError(null);

      const response: AssistantResponse = (
        await api.post(
          "/user/profile/assistant",
          {
            user_id: userId,
            messages,
          },
        )
      );

      const assistantMessage: AssistantMessage = {
        role: "assistant",
        content: response.message,
      };

      setAssistantMessages(
        [
          ...messages,
          assistantMessage,
        ]
      );

      if (
        response.action === "PROPOSE"
        && response.proposed_profile_text
      ) {

        setProfileText(
          response.proposed_profile_text
        );

        setProposalReady(true);

      }

    } catch (error) {

      console.error(
        "Profile assistant error",
        error,
      );

      setAssistantError(
        "The profile assistant is currently unavailable.",
      );

    } finally {

      setAssistantLoading(false);

    }

  }

  /* =====================================================
     START ASSISTANT
  ===================================================== */

  async function startAssistant() {

    if (hasUnsavedChanges) {

      alert(
        "Save or discard the current changes before starting the assistant.",
      );

      return;

    }

    setAssistantOpen(true);
    setAssistantMessages([]);
    setAssistantInput("");
    setAssistantError(null);
    setProposalReady(false);

    await callProfileAssistant(
      []
    );

  }

  /* =====================================================
     SEND ASSISTANT ANSWER
  ===================================================== */

  async function sendAssistantAnswer() {

    const content = (
      assistantInput.trim()
    );

    if (
      !content
      || assistantLoading
      || proposalReady
    ) {

      return;

    }

    const nextMessages: AssistantMessage[] = [
      ...assistantMessages,
      {
        role: "user",
        content,
      },
    ];

    setAssistantMessages(
      nextMessages
    );

    setAssistantInput("");

    await callProfileAssistant(
      nextMessages
    );

  }

  /* =====================================================
     CLOSE ASSISTANT
  ===================================================== */

  function closeAssistant() {

    setAssistantOpen(false);
    setAssistantMessages([]);
    setAssistantInput("");
    setAssistantError(null);
    setProposalReady(false);

  }

  /* =====================================================
     STATUS
  ===================================================== */

  function getStatusClasses() {

    if (
      structuredStatus === "READY"
    ) {

      return (
        "bg-emerald-50 text-emerald-700"
      );

    }

    if (
      structuredStatus === "ERROR"
    ) {

      return (
        "bg-red-50 text-red-700"
      );

    }

    if (
      structuredStatus === "STALE"
    ) {

      return (
        "bg-amber-50 text-amber-700"
      );

    }

    return (
      "bg-gray-100 text-gray-600"
    );

  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <CardSection
      title="Profile"
      description="Build a precise profile to personalize content selection, analyses and Digests."
    >

      {loading ? (

        <div
          className="
            text-sm
            text-gray-500
          "
        >
          Loading...
        </div>

      ) : (

        <div
          className="
            space-y-6
          "
        >

          {/* ===============================================
              STRUCTURED PROFILE STATUS
          =============================================== */}

          <div
            className="
              flex
              flex-wrap
              items-center
              justify-between
              gap-3
              rounded-lg
              border
              border-gray-200
              bg-gray-50
              p-4
            "
          >

            <div>

              <div
                className="
                  flex
                  flex-wrap
                  items-center
                  gap-2
                "
              >

                <span
                  className="
                    text-sm
                    font-medium
                    text-gray-900
                  "
                >
                  Structured profile
                </span>

                <span
                  className={`
                    rounded-full
                    px-2.5
                    py-1
                    text-xs
                    font-medium
                    ${getStatusClasses()}
                  `}
                >
                  {structuredStatus
                    || "Not generated"}
                </span>

              </div>

              <div
                className="
                  mt-1
                  text-xs
                  text-gray-500
                "
              >
                {structuredAt
                  ? `Generated on ${new Date(
                      structuredAt,
                    ).toLocaleString()}`
                  : "No structured profile generated yet."}
              </div>

              {(
                schemaVersion
                || transformerVersion
              ) && (

                <div
                  className="
                    mt-1
                    text-xs
                    text-gray-400
                  "
                >
                  Schema {schemaVersion || "—"}
                  {" · "}
                  Transformer {transformerVersion || "—"}
                </div>

              )}

            </div>

            <button
              type="button"
              onClick={
                regenerateProfile
              }
              disabled={
                regenerating
                || saving
                || !savedProfileText.trim()
              }
              className="
                rounded-lg
                border
                border-gray-300
                bg-white
                px-3
                py-2
                text-xs
                font-medium
                text-gray-700
                transition
                hover:bg-gray-100
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {regenerating
                ? "Regenerating..."
                : "Regenerate"}
            </button>

          </div>

          {structuredError && (

            <div
              className="
                rounded-lg
                border
                border-red-200
                bg-red-50
                p-3
                text-sm
                text-red-700
              "
            >
              {structuredError}
            </div>

          )}

          {/* ===============================================
              PROFILE TEXT
          =============================================== */}

          <div>

            <div
              className="
                mb-3
                flex
                flex-wrap
                items-center
                justify-between
                gap-3
              "
            >

              <div>

                <div
                  className="
                    text-sm
                    font-medium
                    text-gray-900
                  "
                >
                  Professional profile
                </div>

                <div
                  className="
                    mt-1
                    text-xs
                    text-gray-500
                  "
                >
                  This text remains editable before validation.
                </div>

              </div>

              <button
                type="button"
                onClick={
                  assistantOpen
                    ? closeAssistant
                    : startAssistant
                }
                disabled={
                  assistantLoading
                  || saving
                }
                className="
                  rounded-lg
                  border
                  border-ratecard-blue
                  bg-white
                  px-4
                  py-2
                  text-sm
                  font-medium
                  text-ratecard-blue
                  transition
                  hover:bg-blue-50
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {assistantOpen
                  ? "Close assistant"
                  : "Improve with GetCurator"}
              </button>

            </div>

            <textarea
              value={
                profileText
              }
              onChange={event =>
                setProfileText(
                  event.target.value
                )
              }
              rows={14}
              className="
                w-full
                rounded-lg
                border
                border-gray-200
                p-4
                text-sm
                leading-6
                outline-none
                transition
                focus:border-ratecard-blue
              "
              placeholder={`Example:

Global Digital Director

Priorities
- eB2B
- Retail Media
- Quick Commerce

Markets
- United States
- Europe

Strategic questions
- Premiumization
- Distribution evolution
- AI in commerce`}
            />

            {hasUnsavedChanges && (

              <div
                className="
                  mt-2
                  text-xs
                  text-amber-600
                "
              >
                Unsaved changes
              </div>

            )}

          </div>

          {/* ===============================================
              PROFILE ASSISTANT
          =============================================== */}

          {assistantOpen && (

            <div
              className="
                space-y-4
                rounded-xl
                border
                border-blue-100
                bg-blue-50/40
                p-4
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
                  GetCurator Profile Assistant
                </div>

                <div
                  className="
                    mt-1
                    text-xs
                    text-gray-500
                  "
                >
                  Answer the questions to build a more precise profile.
                  Nothing is saved before validation.
                </div>

              </div>

              <div
                className="
                  max-h-96
                  space-y-3
                  overflow-y-auto
                  pr-1
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
                          max-w-[85%]
                          whitespace-pre-wrap
                          rounded-xl
                          px-4
                          py-3
                          text-sm
                          leading-6

                          ${
                            message.role === "user"

                              ? `
                                bg-ratecard-blue
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
                      text-sm
                      text-gray-500
                    "
                  >
                    GetCurator is thinking...
                  </div>

                )}

              </div>

              {assistantError && (

                <div
                  className="
                    rounded-lg
                    border
                    border-red-200
                    bg-red-50
                    p-3
                    text-sm
                    text-red-700
                  "
                >
                  {assistantError}
                </div>

              )}

              {!proposalReady ? (

                <div
                  className="
                    flex
                    gap-2
                  "
                >

                  <textarea
                    value={
                      assistantInput
                    }
                    onChange={event =>
                      setAssistantInput(
                        event.target.value
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
                    placeholder="Write your answer..."
                    disabled={
                      assistantLoading
                    }
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
                      outline-none
                      focus:border-ratecard-blue
                      disabled:opacity-50
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
                      bg-ratecard-blue
                      px-4
                      py-2
                      text-sm
                      font-medium
                      text-white
                      transition
                      hover:opacity-90
                      disabled:cursor-not-allowed
                      disabled:opacity-50
                    "
                  >
                    Send
                  </button>

                </div>

              ) : (

                <div
                  className="
                    rounded-lg
                    border
                    border-emerald-200
                    bg-emerald-50
                    p-4
                  "
                >

                  <div
                    className="
                      text-sm
                      font-medium
                      text-emerald-800
                    "
                  >
                    Proposal ready
                  </div>

                  <div
                    className="
                      mt-1
                      text-sm
                      text-emerald-700
                    "
                  >
                    The proposal has been copied into the profile field.
                    You can edit it before validating and saving it.
                  </div>

                </div>

              )}

            </div>

          )}

          {/* ===============================================
              ACTIONS
          =============================================== */}

          <div
            className="
              flex
              flex-wrap
              items-center
              justify-end
              gap-3
            "
          >

            {hasUnsavedChanges && (

              <button
                type="button"
                onClick={() =>
                  setProfileText(
                    savedProfileText
                  )
                }
                disabled={
                  saving
                }
                className="
                  rounded-lg
                  border
                  border-gray-300
                  px-4
                  py-2
                  text-sm
                  font-medium
                  text-gray-700
                  transition
                  hover:bg-gray-50
                  disabled:opacity-50
                "
              >
                Discard changes
              </button>

            )}

            <button
              type="button"
              onClick={
                saveProfile
              }
              disabled={
                saving
                || regenerating
                || !profileText.trim()
                || !hasUnsavedChanges
              }
              className="
                rounded-lg
                bg-ratecard-blue
                px-5
                py-2
                text-sm
                font-medium
                text-white
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {saving
                ? "Generating and saving..."
                : proposalReady
                  ? "Validate and save"
                  : "Save profile"}
            </button>

          </div>

          {/* ===============================================
              STRUCTURED JSON
          =============================================== */}

          {structuredProfile && (

            <details
              className="
                rounded-lg
                border
                border-gray-200
                bg-gray-50
              "
            >

              <summary
                className="
                  cursor-pointer
                  px-4
                  py-3
                  text-sm
                  font-medium
                  text-gray-700
                "
              >
                View structured profile JSON
              </summary>

              <pre
                className="
                  max-h-[500px]
                  overflow-auto
                  border-t
                  border-gray-200
                  p-4
                  text-xs
                  leading-5
                  text-gray-600
                "
              >
                {JSON.stringify(
                  structuredProfile,
                  null,
                  2,
                )}
              </pre>

            </details>

          )}

        </div>

      )}

    </CardSection>

  );

}
