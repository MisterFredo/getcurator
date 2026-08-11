"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useSearchParams,
} from "next/navigation";

import {
  useEntityDrawer,
} from "@/hooks/useEntityDrawer";

import TopicCard from "@/components/topics/TopicCard";
import FavoritesStrip from "@/components/favorites/FavoritesStrip";

import {
  api,
} from "@/lib/api";

export const dynamic =
  "force-dynamic";

/* =========================================================
   TYPES
========================================================= */

type Topic = {

  id_topic: string;

  label: string;

  universes: string[];
  content_count: number;

};

/* =========================================================
   FETCH
========================================================= */

async function fetchTopics():
  Promise<Topic[]> {

  try {

    const json =
      await api.get(
        "/topic/list-curator",
      );

    const data =
      json?.topics ?? [];

    if (!Array.isArray(data)) {

      return [];

    }

    return data.map(
      (topic: any) => ({

        id_topic:
          topic.id_topic,

        label:
          topic.label,

        universes:
          topic.universes ?? [],
        content_count:
          topic.content_count ?? 0,

      }),
    );

  } catch (e) {

    console.error(
      "❌ fetchTopics error:",
      e,
    );

    return [];

  }

}

/* =========================================================
   SORT
========================================================= */

function sortTopics(
  topics: Topic[],
): Topic[] {

  return [...topics].sort(
    (a, b) =>
      a.label.localeCompare(
        b.label,
        "fr",
        {
          sensitivity:
            "base",
        },
      ),
  );

}

/* =========================================================
   GROUP
========================================================= */

function groupByUniverse(
  topics: Topic[],
) {

  const map:
    Record<
      string,
      Topic[]
    > = {};

  topics.forEach(
    (topic) => {

      (
        topic.universes
        || []
      ).forEach(
        (universe) => {

          if (!map[universe]) {

            map[universe] = [];

          }

          map[universe].push(
            topic,
          );

        },
      );

    },
  );

  Object.keys(
    map,
  ).forEach(
    (universe) => {

      map[universe] =
        sortTopics(
          map[universe],
        );

    },
  );

  return map;

}

/* =========================================================
   PAGE
========================================================= */

export default function TopicsPage() {

  const [
    topics,
    setTopics,
  ] = useState<Topic[]>([]);

  const [
    favorites,
    setFavorites,
  ] = useState<string[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    openUniverses,
    setOpenUniverses,
  ] = useState<
    Record<string, boolean>
  >({});

  const searchParams =
    useSearchParams();

  const {
    loadingId,
    setLoadingId,
  } = useEntityDrawer(
    "topic",
    "topic_id",
  );

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    async function load() {

      setLoading(
        true,
      );

      try {

        const [
          data,
          prefsRes,
        ] = await Promise.all([

          fetchTopics(),

          api.get(
            "/user/preferences",
          ),

        ]);

        setTopics(
          data,
        );

        const topicPrefs =
          Array.isArray(
            prefsRes?.preferences?.TOPIC,
          )
            ? prefsRes.preferences.TOPIC
            : [];

        setFavorites(
          topicPrefs,
        );

      } catch (e) {

        console.error(
          "❌ Topics load error:",
          e,
        );

        setTopics(
          [],
        );

        setFavorites(
          [],
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, []);

  /* =========================================================
     AUTO OPEN CURRENT UNIVERSE
  ========================================================= */

  useEffect(() => {

    const topicId =
      searchParams.get(
        "topic_id",
      );

    if (!topicId) {

      return;

    }

    const topic =
      topics.find(
        (item) =>
          item.id_topic
          === topicId,
      );

    if (!topic) {

      return;

    }

    const universe =
      topic.universes?.[0];

    if (!universe) {

      return;

    }

    setOpenUniverses(
      (previous) => ({

        ...previous,

        [universe]:
          true,

      }),
    );

  }, [
    topics,
    searchParams,
  ]);

  /* =========================================================
     TOGGLE FAVORITE
  ========================================================= */

  async function handleToggleFavorite(
    id: string,
    isFavorite: boolean,
  ) {

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "TOPIC",
            value_id: id,
          },
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "TOPIC",
            value_id: id,
          },
        );

      }

      setFavorites(
        (previous) =>
          isFavorite
            ? previous.filter(
                (value) =>
                  value !== id,
              )
            : [
                ...previous,
                id,
              ],
      );

    } catch (e) {

      console.error(
        "❌ favorite error",
        e,
      );

    }

  }

  /* =========================================================
     HELPERS
  ========================================================= */

  function toggleUniverse(
    universe: string,
  ) {

    setOpenUniverses(
      (previous) => ({

        ...previous,

        [universe]:
          !previous[universe],

      }),
    );

  }

  /* =========================================================
     DATA
  ========================================================= */

  const favoriteTopics =
    sortTopics(
      topics.filter(
        (topic) =>
          favorites.includes(
            topic.id_topic,
          ),
      ),
    );

  const otherTopics =
    topics.filter(
      (topic) =>
        !favorites.includes(
          topic.id_topic,
        ),
    );

  const groupedTopics =
    groupByUniverse(
      otherTopics,
    );

  const hasContent =
    topics.length > 0;

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      space-y-8
    ">

      <div>

        <h1 className="
          text-lg
          font-semibold
          text-gray-900
        ">
          Topics
        </h1>

      </div>

      {loading && (

        <p className="
          text-sm
          text-gray-400
        ">
          Loading topics...
        </p>

      )}

      {!loading
        && favoriteTopics.length > 0
        && (

        <FavoritesStrip>

          <div className="
            grid
            grid-cols-3
            sm:grid-cols-4
            md:grid-cols-6
            lg:grid-cols-7
            xl:grid-cols-8
            gap-3
          ">

            {favoriteTopics.map(
              (topic) => (

                <TopicCard

                  key={
                    topic.id_topic
                  }

                  id={
                    topic.id_topic
                  }

                  label={
                    topic.label
                  }

                  universe={
                    topic.universes?.[0]
                  }

                  contentCount={
                    topic.content_count
                  }

                  isLoading={
                    loadingId
                    === topic.id_topic
                  }

                  onClick={() =>
                    setLoadingId(
                      topic.id_topic,
                    )
                  }

                  isFavorite

                  onToggleFavorite={() =>
                    handleToggleFavorite(
                      topic.id_topic,
                      true,
                    )
                  }

                />

              ),
            )}

          </div>

        </FavoritesStrip>

      )}

      {!loading
        && hasContent
        && Object.entries(
          groupedTopics,
        )
          .sort(
            ([a], [b]) =>
              a.localeCompare(
                b,
              ),
          )
          .map(
            ([
              universe,
              items,
            ]) => (

              <section

                key={
                  universe
                }

                className="
                  space-y-2
                "

              >

                <div

                  onClick={() =>
                    toggleUniverse(
                      universe,
                    )
                  }

                  className="
                    flex
                    items-center
                    justify-between
                    cursor-pointer
                    py-2
                    px-1
                    border-b
                    border-gray-100
                    hover:bg-gray-50
                  "

                >

                  <h2 className="
                    text-xs
                    font-semibold
                    uppercase
                    text-gray-500
                  ">

                    {universe}

                  </h2>

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {items.length}

                  </span>

                </div>

                {openUniverses[
                  universe
                ] && (

                  <div className="
                    grid
                    grid-cols-3
                    sm:grid-cols-4
                    md:grid-cols-6
                    lg:grid-cols-7
                    xl:grid-cols-8
                    gap-3
                    pt-2
                  ">

                    {items.map(
                      (topic) => {

                        const isFavorite =
                          favorites.includes(
                            topic.id_topic,
                          );

                        return (

                          <TopicCard

                            key={
                              topic.id_topic
                            }

                            id={
                              topic.id_topic
                            }

                            label={
                              topic.label
                            }

                            universe={
                              universe
                            }

                            contentCount={
                              topic.content_count
                            }

                            isLoading={
                              loadingId
                              === topic.id_topic
                            }

                            onClick={() =>
                              setLoadingId(
                                topic.id_topic,
                              )
                            }

                            isFavorite={
                              isFavorite
                            }

                            onToggleFavorite={() =>
                              handleToggleFavorite(
                                topic.id_topic,
                                isFavorite,
                              )
                            }

                          />

                        );

                      },
                    )}

                  </div>

                )}

              </section>

            ),
          )}

    </div>

  );

}
