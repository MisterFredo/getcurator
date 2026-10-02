"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import type {
  SourceOption,
} from "@/types/source";


/* ============================================================
   TYPES
============================================================ */

type LinkedInPost = {

  author: string;

  activity_type:
    | "SHARED"
    | "RESHARED";

  relative_date: string;

  date_source:
    | string
    | null;

  title: string;

  raw_text: string;

  content_hash: string;

  is_existing: boolean;

  exists_in_raw: boolean;

  duplicate_in_paste: boolean;

};


type AnalyzeResponse = {

  status: string;

  detected: number;

  existing: number;

  new: number;

  posts: LinkedInPost[];

};


type StoreResponse = {

  status: string;

  requested: number;

  stored: number;

  skipped: number;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function LinkedInStudio() {

  /* =========================================================
     SOURCES
  ========================================================= */

  const [
    sources,
    setSources,
  ] = useState<SourceOption[]>([]);

  const [
    sourcesLoading,
    setSourcesLoading,
  ] = useState(true);

  const [
    sourceId,
    setSourceId,
  ] = useState("");


  /* =========================================================
     INPUT
  ========================================================= */

  const [
    sourceText,
    setSourceText,
  ] = useState("");


  /* =========================================================
     ANALYSIS
  ========================================================= */

  const [
    posts,
    setPosts,
  ] = useState<LinkedInPost[]>([]);

  const [
    selectedHashes,
    setSelectedHashes,
  ] = useState<Set<string>>(
    new Set(),
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    storing,
    setStoring,
  ] = useState(false);

  const [
    analyzed,
    setAnalyzed,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");


  /* =========================================================
     LOAD LINKEDIN SOURCES
  ========================================================= */

  useEffect(() => {

    let cancelled = false;

    async function loadSources() {

      try {

        setSourcesLoading(true);

        const res =
          await api.get(
            "/source/list",
          );

        const allSources:
          SourceOption[] =
            res.sources || [];

        const linkedinSources =
          allSources.filter(
            (source) =>
              source.acquisition_mode ===
              "LINKEDIN_PROFILE",
          );

        if (cancelled) {
          return;
        }

        setSources(
          linkedinSources,
        );

      } catch (e) {

        console.error(
          "Unable to load LinkedIn sources",
          e,
        );

        if (!cancelled) {

          setError(
            "Impossible de charger les sources LinkedIn.",
          );

        }

      } finally {

        if (!cancelled) {

          setSourcesLoading(
            false,
          );

        }

      }

    }

    loadSources();

    return () => {

      cancelled = true;

    };

  }, []);


  /* =========================================================
     SELECTED SOURCE
  ========================================================= */

  const selectedSource =
    useMemo(
      () =>
        sources.find(
          (source) =>
            source.source_id ===
            sourceId,
        ) || null,
      [
        sources,
        sourceId,
      ],
    );


  /* =========================================================
     NEW POSTS
  ========================================================= */

  const newPosts =
    useMemo(
      () =>
        posts.filter(
          (post) =>
            !post.is_existing &&
            !post.duplicate_in_paste,
        ),
      [posts],
    );


  /* =========================================================
     EXISTING POSTS
  ========================================================= */

  const existingPosts =
    useMemo(
      () =>
        posts.filter(
          (post) =>
            post.is_existing,
        ),
      [posts],
    );


  /* =========================================================
     DUPLICATES IN PASTE
  ========================================================= */

  const duplicatePosts =
    useMemo(
      () =>
        posts.filter(
          (post) =>
            post.duplicate_in_paste,
        ),
      [posts],
    );


  /* =========================================================
     SELECTED POSTS
  ========================================================= */

  const selectedPosts =
    useMemo(
      () =>
        newPosts.filter(
          (post) =>
            selectedHashes.has(
              post.content_hash,
            ),
        ),
      [
        newPosts,
        selectedHashes,
      ],
    );


  /* =========================================================
     RESET ANALYSIS
  ========================================================= */

  function resetAnalysis() {

    setPosts([]);

    setSelectedHashes(
      new Set(),
    );

    setAnalyzed(false);

    setError("");

  }


  /* =========================================================
     SOURCE CHANGE
  ========================================================= */

  function handleSourceChange(
    nextSourceId: string,
  ) {

    setSourceId(
      nextSourceId,
    );

    resetAnalysis();

  }


  /* =========================================================
     TEXT CHANGE
  ========================================================= */

  function handleTextChange(
    value: string,
  ) {

    setSourceText(
      value,
    );

    /*
     * If the pasted activity changes after an
     * analysis, the old results are no longer
     * valid.
     */

    if (analyzed) {

      resetAnalysis();

    }

  }


  /* =========================================================
     ANALYZE
  ========================================================= */

  async function analyze() {

    if (!sourceId) {

      alert(
        "Sélectionne une source LinkedIn.",
      );

      return;
    }

    if (!sourceText.trim()) {

      alert(
        "Colle l'activité Sales Navigator.",
      );

      return;
    }

    setLoading(true);

    setError("");

    try {

      /*
       * IMPORTANT:
       *
       * The backend endpoint expects text/plain,
       * not JSON.
       */

      const res =
        await api.postText(
          `/discovery/linkedin-studio/analyze/${sourceId}`,
          sourceText,
        ) as AnalyzeResponse;

      const nextPosts =
        res.posts || [];

      setPosts(
        nextPosts,
      );

      /*
       * New posts are selected by default.
       *
       * Existing RAW contents and duplicates
       * inside the pasted block are excluded.
       */

      setSelectedHashes(
        new Set(
          nextPosts
            .filter(
              (post) =>
                !post.is_existing &&
                !post.duplicate_in_paste,
            )
            .map(
              (post) =>
                post.content_hash,
            ),
        ),
      );

      setAnalyzed(true);

    } catch (e) {

      console.error(
        "LinkedIn analyze error",
        e,
      );

      setError(
        "Erreur pendant l'analyse de l'activité LinkedIn.",
      );

    } finally {

      setLoading(false);

    }

  }


  /* =========================================================
     TOGGLE POST
  ========================================================= */

  function togglePost(
    contentHash: string,
  ) {

    setSelectedHashes(
      (current) => {

        const next =
          new Set(current);

        if (
          next.has(
            contentHash,
          )
        ) {

          next.delete(
            contentHash,
          );

        } else {

          next.add(
            contentHash,
          );

        }

        return next;

      },
    );

  }


  /* =========================================================
     SELECT ALL
  ========================================================= */

  function selectAll() {

    setSelectedHashes(
      new Set(
        newPosts.map(
          (post) =>
            post.content_hash,
        ),
      ),
    );

  }


  /* =========================================================
     UNSELECT ALL
  ========================================================= */

  function unselectAll() {

    setSelectedHashes(
      new Set(),
    );

  }


  /* =========================================================
     STORE
  ========================================================= */

  async function storeSelected() {

    if (!sourceId) {
      return;
    }

    if (
      selectedPosts.length === 0
    ) {

      alert(
        "Aucune publication sélectionnée.",
      );

      return;
    }

    setStoring(true);

    setError("");

    try {

      const res =
        await api.post(
          `/discovery/linkedin-studio/store/${sourceId}`,
          {
            posts:
              selectedPosts.map(
                (post) => ({
                  title:
                    post.title,
                  raw_text:
                    post.raw_text,
                  date_source:
                    post.date_source,
                }),
              ),
          },
        ) as StoreResponse;

      /*
       * Re-run analysis against RAW.
       *
       * This is both useful UX and the final
       * validation of our deduplication loop.
       */

      await analyze();

      alert(
        `${res.stored} publication(s) importée(s).` +
        (
          res.skipped > 0
            ? ` ${res.skipped} ignorée(s).`
            : ""
        ),
      );

    } catch (e) {

      console.error(
        "LinkedIn store error",
        e,
      );

      setError(
        "Erreur pendant l'import des publications LinkedIn.",
      );

    } finally {

      setStoring(false);

    }

  }


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="space-y-8">

      {/* =====================================================
          INPUT
      ====================================================== */}

      <div
        className="
          bg-white
          border
          rounded
          p-6
          space-y-6
        "
      >

        {/* SOURCE */}

        <div>

          <label
            className="
              block
              text-sm
              font-medium
              mb-2
            "
          >
            LinkedIn source
          </label>

          <select
            value={sourceId}
            onChange={(e) =>
              handleSourceChange(
                e.target.value,
              )
            }
            disabled={
              sourcesLoading
            }
            className="
              border
              rounded
              px-3
              py-2
              w-full
              text-sm
              bg-white
              disabled:opacity-50
            "
          >

            <option value="">

              {sourcesLoading
                ? "Loading sources..."
                : "Select a LinkedIn source"}

            </option>

            {sources.map(
              (source) => (

                <option
                  key={
                    source.source_id
                  }
                  value={
                    source.source_id
                  }
                >
                  {source.name}
                </option>

              ),
            )}

          </select>


          {selectedSource?.domain && (

            <div
              className="
                mt-2
                text-xs
                text-gray-400
              "
            >
              {selectedSource.domain}
            </div>

          )}


          {!sourcesLoading &&
            sources.length === 0 && (

            <div
              className="
                mt-2
                text-sm
                text-amber-600
              "
            >
              No source with acquisition mode
              {" "}
              LINKEDIN_PROFILE found.
            </div>

          )}

        </div>


        {/* PASTE */}

        <div>

          <div
            className="
              flex
              items-center
              justify-between
              mb-2
            "
          >

            <label
              className="
                block
                text-sm
                font-medium
              "
            >
              Sales Navigator activity
            </label>

            {sourceText && (

              <button
                type="button"
                onClick={() => {

                  setSourceText("");

                  resetAnalysis();

                }}
                className="
                  text-xs
                  text-gray-500
                  underline
                "
              >
                Clear
              </button>

            )}

          </div>

          <textarea
            value={sourceText}
            onChange={(e) =>
              handleTextChange(
                e.target.value,
              )
            }
            placeholder={
              "Copy the full activity from Sales Navigator and paste it here."
            }
            rows={14}
            className="
              border
              rounded
              px-3
              py-3
              w-full
              text-sm
              font-mono
            "
          />

        </div>


        {/* ANALYZE */}

        <div
          className="
            flex
            justify-end
          "
        >

          <button
            type="button"
            onClick={analyze}
            disabled={
              loading ||
              !sourceId ||
              !sourceText.trim()
            }
            className="
              px-5
              py-2
              bg-ratecard-blue
              text-white
              rounded
              text-sm
              disabled:opacity-50
            "
          >

            {loading
              ? "Analyzing..."
              : "Analyze"}

          </button>

        </div>

      </div>


      {/* =====================================================
          ERROR
      ====================================================== */}

      {error && (

        <div
          className="
            border
            border-red-200
            bg-red-50
            text-red-700
            rounded
            p-4
            text-sm
          "
        >
          {error}
        </div>

      )}


      {/* =====================================================
          RESULTS
      ====================================================== */}

      {analyzed && (

        <div className="space-y-6">

          {/* SUMMARY */}

          <div
            className="
              bg-white
              border
              rounded
              p-5
              flex
              items-center
              justify-between
              gap-6
            "
          >

            <div>

              <div
                className="
                  text-lg
                  font-semibold
                "
              >
                {posts.length} publications detected
              </div>

              <div
                className="
                  text-sm
                  text-gray-500
                  mt-1
                "
              >

                {newPosts.length} new

                {" · "}

                {existingPosts.length} already imported

                {duplicatePosts.length > 0 && (
                  <>
                    {" · "}
                    {duplicatePosts.length} duplicate
                    {duplicatePosts.length > 1
                      ? "s"
                      : ""}
                    {" in paste"}
                  </>
                )}

              </div>

            </div>


            {newPosts.length > 0 && (

              <div
                className="
                  flex
                  items-center
                  gap-4
                "
              >

                <button
                  type="button"
                  onClick={selectAll}
                  className="
                    text-sm
                    underline
                  "
                >
                  Select all
                </button>

                <button
                  type="button"
                  onClick={unselectAll}
                  className="
                    text-sm
                    underline
                  "
                >
                  Unselect all
                </button>

              </div>

            )}

          </div>


          {/* =================================================
              POSTS
          ================================================== */}

          <div className="space-y-3">

            {posts.map(
              (
                post,
                index,
              ) => {

                const disabled =
                  post.is_existing ||
                  post.duplicate_in_paste;

                const selected =
                  selectedHashes.has(
                    post.content_hash,
                  );

                return (

                  <div
                    key={
                      `${post.content_hash}-${index}`
                    }
                    className={`
                      border
                      rounded
                      p-5
                      bg-white
                      ${
                        disabled
                          ? "opacity-50"
                          : ""
                      }
                    `}
                  >

                    <div
                      className="
                        flex
                        gap-4
                        items-start
                      "
                    >

                      {/* CHECKBOX */}

                      <input
                        type="checkbox"
                        checked={
                          !disabled &&
                          selected
                        }
                        disabled={
                          disabled
                        }
                        onChange={() =>
                          togglePost(
                            post.content_hash,
                          )
                        }
                        className="mt-1"
                      />


                      {/* CONTENT */}

                      <div
                        className="
                          min-w-0
                          flex-1
                        "
                      >

                        {/* META */}

                        <div
                          className="
                            flex
                            flex-wrap
                            items-center
                            gap-3
                            mb-2
                          "
                        >

                          <span
                            className="
                              text-xs
                              font-medium
                              uppercase
                            "
                          >
                            {
                              post.activity_type
                            }
                          </span>


                          <span
                            className="
                              text-xs
                              text-gray-400
                            "
                          >
                            {
                              post.date_source ||
                              post.relative_date
                            }
                          </span>


                          {post.is_existing && (

                            <span
                              className="
                                text-xs
                                px-2
                                py-1
                                rounded
                                bg-gray-100
                                text-gray-600
                              "
                            >
                              Already imported
                            </span>

                          )}


                          {!post.is_existing &&
                            post.duplicate_in_paste && (

                            <span
                              className="
                                text-xs
                                px-2
                                py-1
                                rounded
                                bg-amber-50
                                text-amber-700
                              "
                            >
                              Duplicate
                            </span>

                          )}


                          {!post.is_existing &&
                            !post.duplicate_in_paste && (

                            <span
                              className="
                                text-xs
                                px-2
                                py-1
                                rounded
                                bg-green-50
                                text-green-700
                              "
                            >
                              New
                            </span>

                          )}

                        </div>


                        {/* TITLE */}

                        <div
                          className="
                            text-sm
                            font-medium
                          "
                        >
                          {post.title}
                        </div>


                        {/* BODY */}

                        <div
                          className="
                            mt-3
                            text-sm
                            text-gray-600
                            whitespace-pre-wrap
                            line-clamp-5
                          "
                        >
                          {post.raw_text}
                        </div>

                      </div>

                    </div>

                  </div>

                );

              },
            )}

          </div>


          {/* =================================================
              STORE BAR
          ================================================== */}

          {newPosts.length > 0 && (

            <div
              className="
                sticky
                bottom-4
                z-10
                bg-white
                border
                rounded
                shadow-lg
                p-4
                flex
                items-center
                justify-between
                gap-6
              "
            >

              <div
                className="
                  text-sm
                "
              >

                <strong>
                  {selectedPosts.length}
                </strong>

                {" "}

                publication
                {selectedPosts.length !== 1
                  ? "s"
                  : ""}
                {" "}
                selected

              </div>


              <button
                type="button"
                onClick={
                  storeSelected
                }
                disabled={
                  storing ||
                  selectedPosts.length === 0
                }
                className="
                  px-5
                  py-2
                  bg-ratecard-blue
                  text-white
                  rounded
                  text-sm
                  disabled:opacity-50
                "
              >

                {storing
                  ? "Importing..."
                  : (
                    `Import ${selectedPosts.length}`
                  )}

              </button>

            </div>

          )}

        </div>

      )}

    </div>

  );

}
