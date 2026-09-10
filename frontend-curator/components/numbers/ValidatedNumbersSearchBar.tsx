"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  query: string;

  loading?: boolean;

  onSearch: (
    query: string,
  ) => void;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function ValidatedNumbersSearchBar({

  query,

  loading = false,

  onSearch,

}: Props) {

  const [
    input,
    setInput,
  ] = useState(
    query,
  );


  /* ========================================================
     SYNCHRONIZE EXTERNAL QUERY
  ======================================================== */

  useEffect(() => {

    setInput(
      query,
    );

  }, [
    query,
  ]);


  /* ========================================================
     SUBMIT
  ======================================================== */

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {

    event.preventDefault();

    if (loading) {

      return;

    }

    onSearch(
      input.trim(),
    );

  }


  /* ========================================================
     CLEAR
  ======================================================== */

  function handleClear() {

    setInput("");

    onSearch("");

  }


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <form

      onSubmit={
        handleSubmit
      }

      className="
        flex
        w-full
        items-center
        gap-3
      "

    >

      <input

        type="search"

        value={
          input
        }

        disabled={
          loading
        }

        onChange={event =>
          setInput(
            event.target.value,
          )
        }

        placeholder="Search a company, topic, metric or market..."

        className="
          min-w-0
          flex-1
          rounded-xl
          border
          border-gray-200
          bg-white
          px-4
          py-3
          text-sm
          text-gray-900
          outline-none
          transition
          placeholder:text-gray-400
          focus:border-gray-400
          focus:ring-2
          focus:ring-gray-100
          disabled:cursor-not-allowed
          disabled:bg-gray-50
        "

      />

      {input && (

        <button

          type="button"

          disabled={
            loading
          }

          onClick={
            handleClear
          }

          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            px-4
            py-3
            text-sm
            font-medium
            text-gray-600
            transition
            hover:bg-gray-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "

        >

          Clear

        </button>

      )}

      <button

        type="submit"

        disabled={
          loading
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
          disabled:opacity-50
        "

      >

        {loading
          ? "Searching..."
          : "Search"}

      </button>

    </form>

  );

}
