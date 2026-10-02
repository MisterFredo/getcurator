"use client";

import {
  useMemo,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";


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


/* ============================================================
   COMPONENT
============================================================ */

export default function LinkedInStudio() {

  /* =========================================================
     SOURCE
  ========================================================= */

  const [
    sourceId,
    setSourceId,
  ] = useState("");

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
    new Set()
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
     DERIVED
  ========================================================= */

  const newPosts = useMemo(
    () =>
      posts.filter(
        (post) =>
          !post.is_existing
      ),
    [posts]
  );


  const existingPosts = useMemo(
    () =>
      posts.filter(
        (post) =>
          post.is_existing
      ),
    [posts]
  );


  const selectedPosts = useMemo(
    () =>
      newPosts.filter(
        (post) =>
          selectedHashes.has(
            post.content_hash
          )
      ),
    [
      newPosts,
      selectedHashes,
    ]
  );


  /* =========================================================
     ANALYZE
  ========================================================= */

  async function analyze() {

    if (!sourceId.trim()) {

      alert(
        "Sélectionne une source LinkedIn."
      );

      return;
    }

    if (!sourceText.trim()) {

      alert(
        "Colle l'activité Sales Navigator."
      );

      return;
    }

    setLoading(true);
    setError("");
    setAnalyzed(false);

    try {

      const res =
        await api.post(
          `/discovery/linkedin-studio/analyze/${sourceId}`,
          sourceText,
          {
            headers: {
              "Content-Type":
                "text/plain",
            },
          }
        ) as AnalyzeResponse;

      const nextPosts =
        res.posts || [];

      setPosts(
        nextPosts
      );

      /*
       * All genuinely new posts are selected
       * by default.
       */

      setSelectedHashes(
        new Set(
          nextPosts
            .filter(
              (post) =>
                !post.is_existing
            )
            .map(
              (post) =>
                post.content_hash
            )
        )
      );

      setAnalyzed(true);

    } catch (e) {

      console.error(e);

      setError(
        "Erreur pendant l'analyse LinkedIn."
      );

    } finally {

      setLoading(false);

    }
  }


  /* =========================================================
     TOGGLE
  ========================================================= */

  function togglePost(
    contentHash: string
  ) {

    setSelectedHashes(
      (current) => {

        const next =
          new Set(current);

        if (
          next.has(
            contentHash
          )
        ) {

          next.delete(
            contentHash
          );

        } else {

          next.add(
            contentHash
          );

        }

        return next;
      }
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
            post.content_hash
        )
      )
    );
  }


  /* =========================================================
     UNSELECT ALL
  ========================================================= */

  function unselectAll() {

    setSelectedHashes(
      new Set()
    );
  }


  /* =========================================================
     STORE
  ========================================================= */

  async function storeSelected() {

    if (
      !sourceId ||
      !selectedPosts.length
    ) {
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
                })
              ),
          }
        );

      alert(
        `${res.stored} publication(s) importée(s).`
      );

      /*
       * Re-analyze the exact same pasted
       * activity after storage.
       *
       * This immediately verifies RAW
       * deduplication and refreshes the UI.
       */

      await analyze();

    } catch (e) {

      console.error(e);

      setError(
        "Erreur pendant l'import LinkedIn."
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

        <div>

          <label
            className="
              block
              text-sm
              font-medium
              mb-2
            "
          >
            Source ID
          </label>

          <input
            type="text"
            value={sourceId}
            onChange={(e) =>
              setSourceId(
                e.target.value
              )
            }
            placeholder="SOURCE_ID LinkedIn"
            className="
              border
              rounded
              px-3
              py-2
              w-full
              text-sm
            "
          />

        </div>


        <div>

          <label
            className="
              block
              text-sm
              font-medium
              mb-2
            "
          >
            Sales Navigator activity
          </label>

          <textarea
            value={sourceText}
            onChange={(e) =>
              setSourceText(
                e.target.value
              )
            }
            placeholder={
              "Copier toute l'activité du profil Sales Navigator puis la coller ici."
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


        <div
          className="
            flex
            justify-end
          "
        >

          <button
            type="button"
            onClick={analyze}
            disabled={loading}
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
              ? "Analyse..."
              : "Analyser"}

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
                {posts.length} publications détectées
              </div>

              <div
                className="
                  text-sm
                  text-gray-500
                  mt-1
                "
              >
                {newPosts.length} nouvelles
                {" · "}
                {existingPosts.length} déjà importées
              </div>

            </div>


            <div
              className="
                flex
                gap-3
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
                Tout sélectionner
              </button>

              <button
                type="button"
                onClick={unselectAll}
                className="
                  text-sm
                  underline
                "
              >
                Tout désélectionner
              </button>

            </div>

          </div>


          {/* POSTS */}

          <div className="space-y-3">

            {posts.map(
              (post) => {

                const disabled =
                  post.is_existing;

                const selected =
                  selectedHashes.has(
                    post.content_hash
                  );

                return (

                  <div
                    key={
                      post.content_hash
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
                            post.content_hash
                          )
                        }
                        className="mt-1"
                      />


                      <div
                        className="
                          min-w-0
                          flex-1
                        "
                      >

                        <div
                          className="
                            flex
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

                          {disabled ? (

                            <span
                              className="
                                text-xs
                                px-2
                                py-1
                                rounded
                                bg-gray-100
                                text-gray-500
                              "
                            >
                              Déjà importé
                            </span>

                          ) : (

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
                              Nouveau
                            </span>

                          )}

                        </div>


                        <div
                          className="
                            font-medium
                            text-sm
                          "
                        >
                          {post.title}
                        </div>


                        <div
                          className="
                            mt-3
                            text-sm
                            text-gray-600
                            whitespace-pre-wrap
                            line-clamp-4
                          "
                        >
                          {post.raw_text}
                        </div>

                      </div>

                    </div>

                  </div>

                );
              }
            )}

          </div>


          {/* STORE */}

          <div
            className="
              sticky
              bottom-4
              bg-white
              border
              rounded
              shadow-lg
              p-4
              flex
              items-center
              justify-between
            "
          >

            <div className="text-sm">

              <strong>
                {selectedPosts.length}
              </strong>
              {" "}
              publication(s) sélectionnée(s)

            </div>


            <button
              type="button"
              onClick={
                storeSelected
              }
              disabled={
                storing ||
                !selectedPosts.length
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
                ? "Import..."
                : `Importer ${selectedPosts.length}`}

            </button>

          </div>

        </div>

      )}

    </div>

  );
}
