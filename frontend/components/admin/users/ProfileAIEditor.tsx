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

  profile_editorial_text?:
    | string
    | null;

  profile_editorial_status?:
    | string
    | null;

  profile_editorial_error?:
    | string
    | null;

  profile_editorial_at?:
    | string
    | null;

  profile_editorial_transformer_version?:
    | string
    | null;

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

  role:
    | "user"
    | "assistant";

  content: string;

};

type AssistantResponse = {

  status: string;

  assistant_version: string;

  action:
    | "ASK"
    | "PROPOSE";

  message: string;

  proposed_profile_text?:
    | string
    | null;

  profile_complete: boolean;

};


/* =========================================================
   HELPERS
========================================================= */

function getStatusClasses(
  status?: string | null,
): string {

  if (status === "READY") {

    return (
      "bg-emerald-50 text-emerald-700"
    );

  }

  if (status === "ERROR") {

    return (
      "bg-red-50 text-red-700"
    );

  }

  if (status === "STALE") {

    return (
      "bg-amber-50 text-amber-700"
    );

  }

  if (status === "BUILDING") {

    return (
      "bg-blue-50 text-blue-700"
    );

  }

  return (
    "bg-gray-100 text-gray-600"
  );

}


function formatGeneratedAt(
  value?: string | null,
): string {

  if (!value) {

    return (
      "Not generated yet."
    );

  }

  const date = new Date(
    value,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {

    return (
      "Generation date unavailable."
    );

  }

  return (
    `Generated on ${date.toLocaleString()}`
  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function ProfileAIEditor({
  userId,
}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    regenerating,
    setRegenerating,
  ] = useState(false);

  /* =====================================================
     PUBLIC PROFILE
  ===================================================== */

  const [
    profileText,
    setProfileText,
  ] = useState("");

  const [
    savedProfileText,
    setSavedProfileText,
  ] = useState("");

  /* =====================================================
     EDITORIAL PROFILE
  ===================================================== */

  const [
    editorialProfileText,
    setEditorialProfileText,
  ] = useState("");

  const [savedEditorialProfileText, setSavedEditorialProfileText] = useState("");
  const [savingEditorial, setSavingEditorial] = useState(false);
  const [editorialSaveError, setEditorialSaveError] = useState<string | null>(null);
  const hasEditorialChanges = editorialProfileText !== savedEditorialProfileText;

  const [
    editorialStatus,
    setEditorialStatus,
  ] = useState<
    string | null
  >(null);

  const [
    editorialError,
    setEditorialError,
  ] = useState<
    string | null
  >(null);

  const [
    editorialAt,
    setEditorialAt,
  ] = useState<
    string | null
  >(null);

  const [
    editorialTransformerVersion,
    setEditorialTransformerVersion,
  ] = useState<
    string | null
  >(null);

  /* =====================================================
     STRUCTURED PROFILE
  ===================================================== */

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

  /* =====================================================
     ASSISTANT
  ===================================================== */

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

      if (!userId) {

        return;

      }

      try {

        setLoading(true);

        const response = await api.get(
          `/user/profile/admin/${userId}`,
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

        setEditorialProfileText(
          profile.profile_editorial_text
          ?? ""
        );

        setSavedEditorialProfileText(profile.profile_editorial_text ?? "");
        setEditorialSaveError(null);

        setEditorialStatus(
          profile.profile_editorial_status
          ?? null
        );

        setEditorialError(
          profile.profile_editorial_error
          ?? null
        );

        setEditorialAt(
          profile.profile_editorial_at
          ?? null
        );

        setEditorialTransformerVersion(
          profile
            .profile_editorial_transformer_version
          ?? null
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
     SAVE PUBLIC PROFILE
  ===================================================== */

  async function saveProfile() {

    if (hasEditorialChanges) {
      alert("Save or discard the editorial changes before saving the public profile.");
      return;
    }

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
          user_id:
            userId,

          profile_text:
            cleanedProfile,
        },
      );

      await loadProfile();

      setProposalReady(false);

      alert(
        "The public profile and internal profiles were updated. A manually validated editorial mandate is preserved.",
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
     REGENERATE INTERNAL PROFILES
  ===================================================== */

  async function regenerateProfile() {

    if (!savedProfileText.trim()) {

      alert(
        "Save a public profile before regenerating.",
      );

      return;

    }

    if (hasUnsavedChanges || hasEditorialChanges) {

      alert(
        "Save or discard the current changes before regenerating.",
      );

      return;

    }

    try {

      setRegenerating(true);

      const proposal = await api.post(
        "/user/profile/admin/editorial/propose",
        {
          user_id:
            userId,

          force:
            true,
        },
      );

      if (!proposal?.profile_editorial_text?.trim()) {
        throw new Error("Empty editorial proposal");
      }
      setEditorialProfileText(proposal.profile_editorial_text);
      setEditorialSaveError(null);
      alert("Proposal ready. Review the editorial text, then save it to rebuild the JSON.");

    } catch (error) {

      console.error(
        "Failed to regenerate profile",
        error,
      );

      alert(
        "Unable to regenerate the internal profiles.",
      );

    } finally {

      setRegenerating(false);

    }

  }


  /* =====================================================
     SAVE EDITORIAL PROFILE AND REBUILD JSON
  ===================================================== */

  async function saveEditorialProfile() {
    if (hasUnsavedChanges) {
      alert("Save or discard the public profile changes first.");
      return;
    }
    const text = editorialProfileText.trim();
    if (!text || savingEditorial || saving || regenerating || assistantLoading) return;
    try {
      setSavingEditorial(true);
      setEditorialSaveError(null);
      const response = await api.post("/user/profile/admin/editorial/update", {
        user_id: userId,
        profile_editorial_text: text,
      });
      await loadProfile();
      if (response.status === "editorial_saved_structured_error") {
        setEditorialSaveError("Editorial text saved, but JSON generation failed. Save again to retry. " + (response.structured_error || ""));
      } else {
        alert("Editorial profile saved and JSON rebuilt.");
      }
    } catch (error) {
      console.error("Failed to save editorial profile", error);
      setEditorialSaveError("Unable to complete the save. Your draft remains in this field; retry the save.");
    } finally {
      setSavingEditorial(false);
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
            user_id:
              userId,

            messages,
          },
        )
      );

      const assistantMessage:
        AssistantMessage = {

          role:
            "assistant",

          content:
            response.message,

        };

      setAssistantMessages(
        [
          ...messages,
          assistantMessage,
        ],
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

    if (hasUnsavedChanges || hasEditorialChanges) {

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
      [],
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

    const nextMessages:
        AssistantMessage[] = [

      ...assistantMessages,

      {
        role:
          "user",

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
     LOADING
  ===================================================== */

  if (loading) {

    return (

      <CardSection
        title="Profile"
        description="Build a precise profile to personalize content selection, analyses and Digests."
      >

        <div
          className="
            text-sm
            text-gray-500
          "
        >
          Loading...
        </div>

      </CardSection>

    );

  }


  /* =====================================================
     UI
  ===================================================== */

  return (

    <CardSection
      title="Profile"
      description="Build a precise public profile and generate the internal editorial instructions used by GetCurator."
    >

      <div className="space-y-8">

        {/* =================================================
            PUBLIC PROFILE
        ================================================= */}

        <section className="space-y-4">

          <div
            className="
              flex
              flex-wrap
              items-start
              justify-between
              gap-3
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
                Public professional profile
              </div>

              <div
                className="
                  mt-1
                  max-w-3xl
                  text-xs
                  leading-5
                  text-gray-500
                "
              >
                This is the human-readable version displayed
                in the public interface. It is also the source
                used to generate the internal editorial profile.
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
                || regenerating
                || savingEditorial
                || hasEditorialChanges
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
            disabled={saving || savingEditorial || regenerating || assistantLoading}
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

Head of Global eKey Accounts

Focus
- Wine and spirits eCommerce
- Amazon and quick commerce
- Retail media and measurement

Priority markets
- Europe
- United States`}
          />

          {hasUnsavedChanges && (

            <div
              className="
                text-xs
                text-amber-600
              "
            >
              Unsaved changes
            </div>

          )}

        </section>


        {/* =================================================
            PROFILE ASSISTANT
        ================================================= */}

        {assistantOpen && (

          <section
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
                Answer the questions to build a more precise
                public profile. Nothing is saved before
                validation.
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
                    key={
                      `${message.role}-${index}`
                    }
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

              <div className="flex gap-2">

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
                  The proposal has been copied into the public
                  profile field. You can edit it before saving.
                </div>

              </div>

            )}

          </section>

        )}


        {/* =================================================
            PUBLIC PROFILE ACTIONS
        ================================================= */}

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
                || regenerating
                || savingEditorial
                || hasEditorialChanges
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
                || savingEditorial
                || hasEditorialChanges
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
                : "Save public profile"}
          </button>

        </div>


        {/* =================================================
            INTERNAL PROFILE HEADER
        ================================================= */}

        <div
          className="
            border-t
            border-gray-200
            pt-7
          "
        >

          <div
            className="
              flex
              flex-wrap
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <div
                className="
                  text-base
                  font-semibold
                  text-gray-900
                "
              >
                Internal GetCurator profile
              </div>

              <div
                className="
                  mt-1
                  max-w-3xl
                  text-xs
                  leading-5
                  text-gray-500
                "
              >
                These editorial instructions and structured data
                are used internally for content discovery,
                selection, ranking and personalised analysis.
                They are not displayed in the public interface.
              </div>

            </div>

            <button
              type="button"
              onClick={
                regenerateProfile
              }
              disabled={
                regenerating
                || saving
                || savingEditorial
                || assistantLoading
                || hasEditorialChanges
                || hasUnsavedChanges
                || !savedProfileText.trim()
              }
              className="
                rounded-lg
                border
                border-gray-300
                bg-white
                px-4
                py-2
                text-sm
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
                : "Generate editorial proposal"}
            </button>

          </div>

        </div>


        {/* =================================================
            EDITORIAL PROFILE
        ================================================= */}

        <section className="space-y-3">

          <div
            className="
              rounded-lg
              border
              border-gray-200
              bg-gray-50
              p-4
            "
          >

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
                Editorial profile
              </span>

              <span
                className={`
                  rounded-full
                  px-2.5
                  py-1
                  text-xs
                  font-medium
                  ${getStatusClasses(
                    editorialStatus,
                  )}
                `}
              >
                {editorialStatus
                  || "Not generated"}
              </span>

            </div>

            <div
              className="
                mt-2
                text-xs
                text-gray-500
              "
            >
              {formatGeneratedAt(
                editorialAt,
              )}
            </div>

            {editorialTransformerVersion && (

              <div
                className="
                  mt-1
                  text-xs
                  text-gray-400
                "
              >
                Transformer{" "}
                {editorialTransformerVersion}
              </div>

            )}

          </div>

          {editorialError && (

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
              {editorialError}
            </div>

          )}

          <textarea
            value={editorialProfileText}
            onChange={event => setEditorialProfileText(event.target.value)}
            disabled={saving || savingEditorial || regenerating || assistantLoading}
            rows={24}
            aria-label="Editorial monitoring profile"
            placeholder="Write or paste the detailed editorial mandate here."
            className="w-full rounded-lg border border-gray-200 bg-white p-4 text-sm leading-6 text-gray-700 outline-none focus:border-ratecard-blue disabled:opacity-50"
          />
          <p className="text-xs text-gray-500">
            Edit this mandate directly. Saving rebuilds the JSON from this text.
            AI generation creates a proposal for review.
          </p>
          {hasEditorialChanges && <p className="text-xs text-amber-600">Unsaved editorial changes</p>}
          {editorialSaveError && <p className="text-sm text-red-700">{editorialSaveError}</p>}
          <div className="flex flex-wrap justify-end gap-3">
            {hasEditorialChanges && (
              <button type="button"
                onClick={() => { setEditorialProfileText(savedEditorialProfileText); setEditorialSaveError(null); }}
                disabled={saving || savingEditorial || regenerating || assistantLoading}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm disabled:opacity-50">
                Discard editorial changes
              </button>
            )}
            <button type="button" onClick={saveEditorialProfile}
              disabled={saving || savingEditorial || regenerating || assistantLoading || hasUnsavedChanges || !editorialProfileText.trim()}
              className="rounded-lg bg-ratecard-blue px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
              {savingEditorial ? "Saving and rebuilding JSON..." : "Save editorial profile and rebuild JSON"}
            </button>
          </div>

        </section>


        {/* =================================================
            STRUCTURED PROFILE
        ================================================= */}

        <section className="space-y-3">

          <div
            className="
              rounded-lg
              border
              border-gray-200
              bg-gray-50
              p-4
            "
          >

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
                  ${getStatusClasses(
                    structuredStatus,
                  )}
                `}
              >
                {structuredStatus
                  || "Not generated"}
              </span>

            </div>

            <div
              className="
                mt-2
                text-xs
                text-gray-500
              "
            >
              {formatGeneratedAt(
                structuredAt,
              )}
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
                Schema{" "}
                {schemaVersion || "—"}
                {" · "}
                Transformer{" "}
                {transformerVersion || "—"}
              </div>

            )}

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

          {structuredProfile ? (

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
                  max-h-[600px]
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

          ) : (

            <div
              className="
                rounded-lg
                border
                border-dashed
                border-gray-300
                p-4
                text-sm
                text-gray-500
              "
            >
              No structured profile has been generated yet.
            </div>

          )}

        </section>

      </div>

    </CardSection>

  );

}
