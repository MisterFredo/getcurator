"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  interlocutorId: string;
  interlocutorName: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ConversationResponse = {
  interlocutor_id: string;
  answer: string;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function HomeConversation({

  interlocutorId,

  interlocutorName,

}: Props) {

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
     RESET WHEN INTERLOCUTOR CHANGES
  ========================================================= */

  useEffect(() => {

    setMessages(
      [],
    );

    setQuestion(
      "",
    );

    setError(
      null,
    );

  }, [
    interlocutorId,
  ]);

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
      !interlocutorId
    ) {

      return;

    }

    /*
     * V1:
     * keep the recent conversation
     * in the frontend session.
     */

    const history =
      messages.slice(
        -10,
      );

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
              interlocutorId,

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
        "❌ Home conversation error:",
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

    <section
      className="
        flex
        min-h-[620px]
        flex-col
        rounded-2xl
        border
        border-gray-200
        bg-white
        shadow-sm
      "
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        className="
          border-b
          border-gray-100
          px-5
          py-4
        "
      >

        <div
          className="
            text-xs
            font-medium
            uppercase
            tracking-wide
            text-gray-400
          "
        >
          Conversation
        </div>

        <div
          className="
            mt-1
            text-base
            font-semibold
            text-gray-900
          "
        >
          {interlocutorName}
        </div>

        <p
          className="
            mt-1
            text-xs
            leading-5
            text-gray-500
          "
        >
          Ask questions, challenge ideas
          and go deeper into this profile&apos;s
          expertise.
        </p>

      </div>

      {/* =====================================================
          MESSAGES
      ===================================================== */}

      <div
        className="
          flex-1
          overflow-y-auto
          px-5
          py-5
        "
      >

        {messages.length === 0 ? (

          <div
            className="
              flex
              h-full
              min-h-[360px]
              items-center
              justify-center
              text-center
            "
          >

            <div
              className="
                max-w-sm
              "
            >

              <div
                className="
                  text-base
                  font-medium
                  text-gray-700
                "
              >
                What would you like to explore?
              </div>

              <p
                className="
                  mt-2
                  text-sm
                  leading-6
                  text-gray-400
                "
              >
                Ask {interlocutorName} about
                strategy, trends, mechanisms,
                risks or key figures.
              </p>

            </div>

          </div>

        ) : (

          <div
            className="
              space-y-5
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
                      max-w-[88%]
                      rounded-xl
                      px-4
                      py-3
                      text-sm
                      leading-6

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
                      {message.content}
                    </div>

                  </div>

                </div>

              ),
            )}

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
            mx-5
            mb-3
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-3
            py-2
            text-xs
            text-red-700
          "
        >
          {error}
        </div>

      )}

      {/* =====================================================
          INPUT
      ===================================================== */}

      <div
        className="
          border-t
          border-gray-100
          p-4
        "
      >

        <form
          onSubmit={
            handleSubmit
          }
          className="
            flex
            gap-2
          "
        >

          <textarea

            value={
              question
            }

            onChange={
              event =>
                setQuestion(
                  event.target.value,
                )
            }

            onKeyDown={
              event => {

                if (
                  event.key ===
                    "Enter"
                  &&
                  !event.shiftKey
                ) {

                  event.preventDefault();

                  event.currentTarget
                    .form
                    ?.requestSubmit();

                }

              }
            }

            placeholder={
              `Ask ${interlocutorName}...`
            }

            disabled={
              loading
            }

            rows={
              2
            }

            className="
              min-h-[52px]
              flex-1
              resize-none
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
              !question.trim()
            }

            className="
              self-end
              rounded-xl
              bg-gray-900
              px-4
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

        <div
          className="
            mt-2
            text-[11px]
            text-gray-400
          "
        >
          Enter to send · Shift + Enter for a new line
        </div>

      </div>

    </section>

  );

}
