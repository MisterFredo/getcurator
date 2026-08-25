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

  const [
    interlocutorDescription,
    setInterlocutorDescription,
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
   LOAD INTERLOCUTOR DESCRIPTION
  ========================================================= */
  
  useEffect(() => {
  
    let active = true;
  
    async function loadInterlocutor() {
  
      try {
  
        setInterlocutorDescription(
          null,
        );
  
        const response =
          await api.get(
            `/user/${interlocutorId}`,
          );
  
        if (!active) {
  
          return;
  
        }
  
        setInterlocutorDescription(
          response?.user?.DESCRIPTION
          || null,
        );
  
      } catch (error) {
  
        console.error(
          "Unable to load interlocutor:",
          error,
        );
  
        if (active) {
  
          setInterlocutorDescription(
            null,
          );
  
        }
  
      }
  
    }
  
    if (interlocutorId) {
  
      loadInterlocutor();
  
    }
  
    return () => {
  
      active = false;
  
    };
  
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
        min-h-[800px]
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

        {interlocutorDescription && (

          <p
            className="
              mt-2
              max-w-2xl
              text-sm
              font-medium
              leading-6
              text-gray-700
            "
          >
            {interlocutorDescription}
          </p>
        
        )}
        
        <p
          className="
            mt-2
            text-xs
            leading-5
            text-gray-500
          "
        >
          WATCH shows what’s happening. DIGESTS explain why it matters.
          CONVERSATION helps you connect signals, challenge ideas and go deeper.
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
                Ask {interlocutorName} to explain, compare or challenge an idea.
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
