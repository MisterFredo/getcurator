"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import InterlocutorCard
  from "@/components/conversation/InterlocutorCard";

/* =========================================================
   TYPES
========================================================= */

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ConversationResponse = {
  interlocutor_id: string;
  answer: string;
};

type Interlocutor = {
  id: string;
  displayName: string;
  company?: string | null;
  description?: string | null;
  type: "self" | "expert";
};

type ExpertRow = {
  ID_USER: string;
  DISPLAY_NAME?: string | null;
  NAME?: string | null;
  COMPANY?: string | null;
  DESCRIPTION?: string | null;
  IS_SELECTED?: boolean;
  IS_ACTIVE?: boolean;
};

/* =========================================================
   PAGE
========================================================= */

export default function ConversationPage() {

  const [
    interlocutors,
    setInterlocutors,
  ] = useState<Interlocutor[]>([]);

  const [
    selectedInterlocutorId,
    setSelectedInterlocutorId,
  ] = useState<string | null>(
    null,
  );

  const [
    interlocutorsLoading,
    setInterlocutorsLoading,
  ] = useState(true);

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    messages,
    setMessages,
  ] = useState<Message[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  /* =========================================================
     LOAD INTERLOCUTORS
  ========================================================= */

  useEffect(() => {

    async function loadInterlocutors() {

      setInterlocutorsLoading(
        true,
      );

      try {

        const [
          meRes,
          expertsRes,
        ] = await Promise.all([

          api.get(
            "/user/me",
          ),

          api.get(
            "/user/experts",
          ),

        ]);

        const user =
          meRes?.user;

        if (!user?.ID_USER) {

          setError(
            "Unable to identify the current user.",
          );

          return;

        }

        /* ===============================================
           SELF
        =============================================== */

        const self:
          Interlocutor = {

          id:
            user.ID_USER,

          displayName:
            user.DISPLAY_NAME
            ??
            user.NAME
            ??
            "User",

          company:
            user.COMPANY ?? null,

          description:
            "Your profile, interests and accumulated knowledge.",

          type:
            "self",
        };

        /* ===============================================
           EXPERTS
        =============================================== */

        const expertRows:
          ExpertRow[] =
          Array.isArray(
            expertsRes,
          )
            ? expertsRes
            : expertsRes?.experts ?? [];

        const experts:
          Interlocutor[] =
          expertRows
            .filter(
              expert =>
                expert.IS_SELECTED === true &&
                expert.IS_ACTIVE !== false,
            )
            .map(
              expert => ({

                id:
                  expert.ID_USER,

                displayName:
                  expert.DISPLAY_NAME
                  ??
                  expert.NAME
                  ??
                  "Expert",

                company:
                  expert.COMPANY
                  ?? null,

                description:
                  expert.DESCRIPTION
                  ?? null,

                type:
                  "expert",
              }),
            );

        const available = [
          self,
          ...experts,
        ];

        setInterlocutors(
          available,
        );

        setSelectedInterlocutorId(
          self.id,
        );

      } catch (e) {

        console.error(
          "❌ Interlocutors load error:",
          e,
        );

        setError(
          "Unable to load interlocutors.",
        );

      } finally {

        setInterlocutorsLoading(
          false,
        );

      }

    }

    loadInterlocutors();

  }, []);

  /* =========================================================
     SELECT INTERLOCUTOR
  ========================================================= */

  function handleSelectInterlocutor(
    id: string,
  ) {

    if (
      id ===
      selectedInterlocutorId
    ) {

      return;

    }

    setSelectedInterlocutorId(
      id,
    );

    setMessages(
      [],
    );

    setQuestion(
      "",
    );

    setError(
      null,
    );

  }

  /* =========================================================
     CURRENT INTERLOCUTOR
  ========================================================= */

  const selectedInterlocutor =
    interlocutors.find(
      interlocutor =>
        interlocutor.id ===
        selectedInterlocutorId,
    ) ?? null;

  /* =========================================================
     SEND
  ========================================================= */

  async function handleSubmit(
    event: FormEvent,
  ) {

    event.preventDefault();

    const cleanQuestion =
      question.trim();

    if (
      !cleanQuestion ||
      loading ||
      !selectedInterlocutorId
    ) {

      return;

    }

    const history =
      [...messages];

    const userMessage: Message = {
      role: "user",
      content: cleanQuestion,
    };

    setMessages(
      previous => [
        ...previous,
        userMessage,
      ],
    );

    setQuestion(
      "",
    );

    setError(
      null,
    );

    setLoading(
      true,
    );

    try {

      const response:
        ConversationResponse =
        await api.post(
          "/conversation/",
          {
            interlocutor_id:
              selectedInterlocutorId,

            question:
              cleanQuestion,

            history,
          },
        );

      const assistantMessage:
        Message = {
          role:
            "assistant",

          content:
            response.answer,
        };

      setMessages(
        previous => [
          ...previous,
          assistantMessage,
        ],
      );

    } catch (e) {

      console.error(
        "❌ Conversation error:",
        e,
      );

      setError(
        "Unable to generate an answer.",
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      className="
        mx-auto
        max-w-5xl
        space-y-8
      "
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div>

        <h1
          className="
            text-xl
            font-semibold
            text-gray-900
          "
        >
          Conversation
        </h1>

        <p
          className="
            mt-1
            text-sm
            text-gray-500
          "
        >
          Choose who you want to talk to.
        </p>

      </div>

      {/* =====================================================
          INTERLOCUTORS
      ===================================================== */}

      <div
        className="
          space-y-3
        "
      >

        <div
          className="
            text-sm
            font-medium
            text-gray-700
          "
        >
          Interlocutors
        </div>

        {interlocutorsLoading ? (

          <div
            className="
              text-sm
              text-gray-400
            "
          >
            Loading interlocutors...
          </div>

        ) : (

          <div
            className="
              grid
              grid-cols-1
              gap-3
              sm:grid-cols-2
              lg:grid-cols-3
              xl:grid-cols-4
            "
          >

            {interlocutors.map(
              interlocutor => (

                <InterlocutorCard

                  key={
                    interlocutor.id
                  }

                  id={
                    interlocutor.id
                  }

                  displayName={
                    interlocutor.displayName
                  }

                  company={
                    interlocutor.company
                  }

                  description={
                    interlocutor.description
                  }

                  isSelf={
                    interlocutor.type ===
                    "self"
                  }

                  isSelected={
                    interlocutor.id ===
                    selectedInterlocutorId
                  }

                  onSelect={
                    handleSelectInterlocutor
                  }

                />

              ),
            )}

          </div>

        )}

      </div>

      {/* =====================================================
          ACTIVE INTERLOCUTOR
      ===================================================== */}

      {selectedInterlocutor && (

        <div
          className="
            border-b
            border-gray-200
            pb-4
          "
        >

          <div
            className="
              text-xs
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Conversation with
          </div>

          <div
            className="
              mt-1
              text-lg
              font-semibold
              text-gray-900
            "
          >
            {
              selectedInterlocutor
                .displayName
            }
          </div>

          {
            selectedInterlocutor
              .description
            && (

            <p
              className="
                mt-1
                max-w-2xl
                text-sm
                text-gray-500
              "
            >
              {
                selectedInterlocutor
                  .description
              }
            </p>

          )}

        </div>

      )}

      {/* =====================================================
          CONVERSATION
      ===================================================== */}

      <div
        className="
          min-h-[420px]
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >

        {/* EMPTY */}

        {messages.length === 0 && (

          <div
            className="
              flex
              min-h-[360px]
              items-center
              justify-center
              text-center
            "
          >

            <div>

              <div
                className="
                  text-base
                  font-medium
                  text-gray-700
                "
              >
                What would you like to know?
              </div>

              <div
                className="
                  mt-2
                  text-sm
                  text-gray-400
                "
              >
                Ask your interlocutor
                about their areas of expertise.
              </div>

            </div>

          </div>

        )}

        {/* MESSAGES */}

        {messages.length > 0 && (

          <div
            className="
              space-y-6
            "
          >

            {messages.map(
              (
                message,
                index,
              ) => (

                <div
                  key={index}
                  className={
                    message.role ===
                    "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >

                  <div
                    className={`
                      max-w-[80%]
                      rounded-xl
                      px-4
                      py-3
                      text-sm
                      leading-relaxed

                      ${
                        message.role ===
                        "user"

                          ? `
                            bg-gray-900
                            text-white
                          `

                          : `
                            bg-gray-100
                            text-gray-800
                          `
                      }
                    `}
                  >

                    <div
                      className="
                        whitespace-pre-wrap
                      "
                    >
                      {
                        message.content
                      }
                    </div>

                  </div>

                </div>

              ),
            )}

            {/* LOADING */}

            {loading && (

              <div
                className="
                  flex
                  justify-start
                "
              >

                <div
                  className="
                    rounded-xl
                    bg-gray-100
                    px-4
                    py-3
                    text-sm
                    text-gray-500
                  "
                >
                  Thinking...
                </div>

              </div>

            )}

          </div>

        )}

      </div>

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (

        <div
          className="
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-4
            py-3
            text-sm
            text-red-700
          "
        >
          {error}
        </div>

      )}

      {/* =====================================================
          INPUT
      ===================================================== */}

      <form
        onSubmit={
          handleSubmit
        }
        className="
          flex
          gap-3
        "
      >

        <input

          type="text"

          value={
            question
          }

          onChange={
            event =>
              setQuestion(
                event.target.value,
              )
          }

          placeholder={
            selectedInterlocutor
              ? `Ask ${selectedInterlocutor.displayName}...`
              : "Ask a question..."
          }

          disabled={
            loading ||
            !selectedInterlocutorId
          }

          className="
            flex-1
            rounded-xl
            border
            border-gray-200
            bg-white
            px-4
            py-3
            text-sm
            outline-none
            transition
            focus:border-gray-400
            disabled:bg-gray-50
          "

        />

        <button

          type="submit"

          disabled={
            loading ||
            !question.trim() ||
            !selectedInterlocutorId
          }

          className="
            rounded-xl
            bg-gray-900
            px-5
            py-3
            text-sm
            font-medium
            text-white
            transition
            hover:bg-gray-800
            disabled:cursor-not-allowed
            disabled:opacity-40
          "

        >
          Send
        </button>

      </form>

    </div>

  );

}
