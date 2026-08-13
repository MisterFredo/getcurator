"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

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

/* =========================================================
   PAGE
========================================================= */

export default function ConversationPage() {

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
      loading
    ) {

      return;

    }

    const userId =
      localStorage.getItem(
        "user_id",
      );

    if (!userId) {

      setError(
        "Unable to identify the current user.",
      );

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

    setQuestion("");
    setError(null);
    setLoading(true);

    try {

      const response:
        ConversationResponse =
        await api.post(
          "/conversation/",
          {
            interlocutor_id:
              userId,

            question:
              cleanQuestion,

            history,
          },
        );

      const assistantMessage:
        Message = {
          role: "assistant",
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

      setLoading(false);

    }

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      className="
        mx-auto
        max-w-4xl
        space-y-6
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
          Ask questions to your augmented self.
        </p>

      </div>

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
                Your answers are based on
                your selected interests and
                their Knowledge.
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
                    message.role === "user"
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
                        message.role === "user"

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

          placeholder="
            Ask a question...
          "

          disabled={
            loading
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
            !question.trim()
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
