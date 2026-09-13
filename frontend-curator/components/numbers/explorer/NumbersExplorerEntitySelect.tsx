"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  ChevronDown,
  Search,
  X,
} from "lucide-react";

import type {
  PublicNumberFilterOption,
} from "@/types/numbers";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  label: string;

  placeholder: string;

  value: string;

  options:
    PublicNumberFilterOption[];

  disabled?: boolean;

  onChange: (
    value: string,
  ) => void;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function NumbersExplorerEntitySelect({

  label,

  placeholder,

  value,

  options,

  disabled = false,

  onChange,

}: Props) {

  const containerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    search,
    setSearch,
  ] = useState("");


  /* ========================================================
     SELECTED OPTION
  ======================================================== */

  const selectedOption =
    options.find(
      option =>
        option.value === value,
    )
    || null;


  /* ========================================================
     FILTERED OPTIONS
  ======================================================== */

  const filteredOptions =
    useMemo(
      () => {

        const normalizedSearch =
          search
            .trim()
            .toLocaleLowerCase();

        const result =
          normalizedSearch
            ? options.filter(
                option =>
                  option.label
                    .toLocaleLowerCase()
                    .includes(
                      normalizedSearch,
                    ),
              )
            : options;

        return result.slice(
          0,
          100,
        );

      },
      [
        options,
        search,
      ],
    );


  /* ========================================================
     CLICK OUTSIDE
  ======================================================== */

  useEffect(() => {

    function handleClickOutside(
      event: MouseEvent,
    ) {

      if (
        containerRef.current
        && !containerRef.current.contains(
          event.target as Node,
        )
      ) {

        setOpen(false);

        setSearch("");

      }

    }

    document.addEventListener(
      "mousedown",
      handleClickOutside,
    );

    return () => {

      document.removeEventListener(
        "mousedown",
        handleClickOutside,
      );

    };

  }, []);


  /* ========================================================
     CLOSE IF DISABLED
  ======================================================== */

  useEffect(() => {

    if (disabled) {

      setOpen(false);

      setSearch("");

    }

  }, [
    disabled,
  ]);


  /* ========================================================
     SELECT
  ======================================================== */

  function handleSelect(
    optionValue: string,
  ) {

    onChange(
      optionValue,
    );

    setOpen(false);

    setSearch("");

  }


  /* ========================================================
     CLEAR
  ======================================================== */

  function handleClear() {

    onChange("");

    setOpen(false);

    setSearch("");

  }


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div
      ref={containerRef}
      className="
        relative
        space-y-1
      "
    >

      <span
        className="
          block
          text-[10px]
          font-semibold
          uppercase
          tracking-wide
          text-gray-400
        "
      >
        {label}
      </span>

      <div className="relative">

        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            setOpen(
              current =>
                !current,
            )
          }
          className="
            flex
            w-full
            items-center
            justify-between
            gap-2
            rounded-lg
            border
            border-gray-200
            bg-white
            px-3
            py-2
            text-left
            text-xs
            text-gray-700
            outline-none
            transition
            hover:border-gray-300
            focus:border-gray-400
            disabled:cursor-not-allowed
            disabled:bg-gray-50
          "
        >

          <span
            className={`
              min-w-0
              flex-1
              truncate
              ${
                selectedOption
                  ? "text-gray-800"
                  : "text-gray-400"
              }
            `}
          >
            {selectedOption?.label
              || placeholder}
          </span>

          <ChevronDown
            size={14}
            className={`
              shrink-0
              text-gray-400
              transition-transform
              ${
                open
                  ? "rotate-180"
                  : ""
              }
            `}
          />

        </button>

        {selectedOption && !disabled && (

          <button
            type="button"
            onClick={event => {

              event.stopPropagation();

              handleClear();

            }}
            aria-label={`Clear ${label}`}
            className="
              absolute
              right-8
              top-1/2
              -translate-y-1/2
              rounded
              p-0.5
              text-gray-300
              hover:bg-gray-100
              hover:text-gray-600
            "
          >
            <X size={12} />
          </button>

        )}

      </div>


      {/* ================================================= */}
      {/* DROPDOWN */}
      {/* ================================================= */}

      {open && (

        <div
          className="
            absolute
            left-0
            right-0
            z-30
            mt-1
            overflow-hidden
            rounded-lg
            border
            border-gray-200
            bg-white
            shadow-lg
          "
        >

          <div
            className="
              border-b
              border-gray-100
              p-2
            "
          >

            <div
              className="
                flex
                items-center
                gap-2
                rounded-md
                bg-gray-50
                px-2
              "
            >

              <Search
                size={13}
                className="
                  shrink-0
                  text-gray-400
                "
              />

              <input
                autoFocus
                type="search"
                value={search}
                onChange={event =>
                  setSearch(
                    event.target.value,
                  )
                }
                placeholder={`Search ${label.toLowerCase()}...`}
                className="
                  min-w-0
                  flex-1
                  bg-transparent
                  py-2
                  text-xs
                  text-gray-700
                  outline-none
                  placeholder:text-gray-400
                "
              />

            </div>

          </div>

          <div
            className="
              max-h-64
              overflow-y-auto
              p-1
            "
          >

            <button
              type="button"
              onClick={() =>
                handleSelect("")
              }
              className="
                flex
                w-full
                items-center
                justify-between
                rounded-md
                px-3
                py-2
                text-left
                text-xs
                text-gray-500
                hover:bg-gray-50
              "
            >
              {placeholder}
            </button>

            {filteredOptions.map(
              option => (

                <button
                  key={option.value}
                  type="button"
                  onClick={() =>
                    handleSelect(
                      option.value,
                    )
                  }
                  className={`
                    flex
                    w-full
                    items-center
                    justify-between
                    gap-3
                    rounded-md
                    px-3
                    py-2
                    text-left
                    text-xs
                    transition

                    ${
                      option.value === value
                        ? "bg-gray-100 text-gray-900"
                        : "text-gray-700 hover:bg-gray-50"
                    }
                  `}
                >

                  <span
                    className="
                      min-w-0
                      flex-1
                      truncate
                    "
                  >
                    {option.label}
                  </span>

                  <span
                    className="
                      shrink-0
                      text-[10px]
                      text-gray-400
                    "
                  >
                    {option.count}
                  </span>

                </button>

              ),
            )}

            {filteredOptions.length === 0 && (

              <div
                className="
                  px-3
                  py-6
                  text-center
                  text-xs
                  text-gray-400
                "
              >
                No result
              </div>

            )}

            {filteredOptions.length === 100 && (

              <div
                className="
                  border-t
                  border-gray-100
                  px-3
                  py-2
                  text-center
                  text-[10px]
                  text-gray-400
                "
              >
                Refine your search to see more.
              </div>

            )}

          </div>

        </div>

      )}

    </div>

  );

}
