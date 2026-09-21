"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

/* ============================================================
   TYPES
============================================================ */

type LeftDrawerType =
  | "member"
  | "company"
  | "topic"
  | "solution"
  | "expert"
  | null;

type RightDrawerType =
  | "content"
  | "numbers"
  | "digest"
  | null;

type DrawerMode =
  | "silent"
  | "route";

type DrawerSlot<T> = {

  type: T;

  id: string | null;

  mode: DrawerMode | null;

  payload?: any;

};

type DrawerContextType = {

  leftDrawer:
    DrawerSlot<LeftDrawerType>;

  rightDrawer:
    DrawerSlot<RightDrawerType>;

  openLeftDrawer: (

    type:
      | "member"
      | "company"
      | "topic"
      | "solution"
      | "expert",

    id: string,

    mode?: DrawerMode,

  ) => void;

  openRightDrawer: (

    type:
      | "content"
      | "numbers"
      | "digest",

    id: string,

    mode?: DrawerMode,

    payload?: any,

  ) => void;

  closeLeftDrawer:
    () => void;

  closeRightDrawer:
    () => void;

  setOnLeftClose: (
    fn: (() => void) | null,
  ) => void;

};

/* ============================================================
   CONTEXT
============================================================ */

const DrawerContext =
  createContext<
    DrawerContextType | null
  >(null);

/* ============================================================
   PROVIDER
============================================================ */

export function DrawerProvider({

  children,

}: {

  children: ReactNode;

}) {

  const [

    leftDrawer,

    setLeftDrawer,

  ] = useState<
    DrawerSlot<LeftDrawerType>
  >({

    type: null,

    id: null,

    mode: null,

  });

  const [

    rightDrawer,

    setRightDrawer,

  ] = useState<
    DrawerSlot<RightDrawerType>
  >({

    type: null,

    id: null,

    mode: null,

  });

  const [

    onLeftClose,

    setOnLeftCloseState,

  ] = useState<
    (() => void) | null
  >(null);

  /* ========================================================
     CALLBACK
  ======================================================== */

  function setOnLeftClose(
    fn: (() => void) | null,
  ) {

    setOnLeftCloseState(
      () => fn,
    );

  }

  /* ========================================================
     URL → RIGHT DRAWER
  ======================================================== */

  useEffect(() => {

    function syncRightDrawerFromUrl() {

      const params =
        new URLSearchParams(
          window.location.search,
        );

      /*
       * analysis_id:
       * Historical Digest links.
       *
       * content_id:
       * Optional future unified convention.
       */

      const contentId =
        params.get(
          "analysis_id",
        )
        ??
        params.get(
          "content_id",
        );

      if (contentId) {

        setRightDrawer({

          type:
            "content",

          id:
            contentId,

          mode:
            "route",

        });

        return;

      }

      /*
       * If the drawer was controlled by the URL
       * and the parameter disappears, close it.
       *
       * Silent drawers are not affected.
       */

      setRightDrawer(
        current => {

          if (
            current.mode !== "route"
          ) {

            return current;

          }

          return {

            type: null,

            id: null,

            mode: null,

          };

        },
      );

    }

    /*
     * Open the drawer when arriving from
     * a Digest deep link.
     */

    syncRightDrawerFromUrl();

    /*
     * Synchronize the drawer when the user
     * navigates with browser Back/Forward.
     */

    window.addEventListener(
      "popstate",
      syncRightDrawerFromUrl,
    );

    return () => {

      window.removeEventListener(
        "popstate",
        syncRightDrawerFromUrl,
      );

    };

  }, []);

  /* ========================================================
     LEFT
  ======================================================== */

  function openLeftDrawer(

    type:
      | "member"
      | "company"
      | "topic"
      | "solution"
      | "expert",

    id: string,

    mode: DrawerMode =
      "silent",

  ) {

    setLeftDrawer({

      type,

      id,

      mode,

    });

  }

  function closeLeftDrawer() {

    if (onLeftClose) {

      try {

        onLeftClose();

      } catch (e) {

        console.error(
          e,
        );

      }

    }

    setLeftDrawer({

      type: null,

      id: null,

      mode: null,

    });

  }

  /* ========================================================
     RIGHT
  ======================================================== */

  function openRightDrawer(

    type:
      | "content"
      | "numbers"
      | "digest",

    id: string,

    mode: DrawerMode =
      "silent",

    payload?: any,

  ) {

    /*
     * Route mode makes content drawers
     * addressable and shareable.
     */

    if (
      mode === "route"
      &&
      type === "content"
      &&
      typeof window !== "undefined"
    ) {

      const url =
        new URL(
          window.location.href,
        );

      /*
       * Remove both supported conventions
       * before setting the canonical one.
       */

      url.searchParams.delete(
        "analysis_id",
      );

      url.searchParams.delete(
        "content_id",
      );

      url.searchParams.set(
        "analysis_id",
        id,
      );

      window.history.pushState(

        window.history.state,

        "",

        `${url.pathname}${url.search}${url.hash}`,

      );

    }

    setRightDrawer({

      type,

      id,

      mode,

      payload,

    });

  }

  function closeRightDrawer() {

    /*
     * Remove the URL parameter only when
     * the drawer is controlled by the route.
     */

    if (
      rightDrawer.mode === "route"
      &&
      typeof window !== "undefined"
    ) {

      const url =
        new URL(
          window.location.href,
        );

      url.searchParams.delete(
        "analysis_id",
      );

      url.searchParams.delete(
        "content_id",
      );

      window.history.replaceState(

        window.history.state,

        "",

        `${url.pathname}${url.search}${url.hash}`,

      );

    }

    setRightDrawer({

      type: null,

      id: null,

      mode: null,

    });

  }

  /* ========================================================
     PROVIDER
  ======================================================== */

  return (

    <DrawerContext.Provider

      value={{

        leftDrawer,

        rightDrawer,

        openLeftDrawer,

        openRightDrawer,

        closeLeftDrawer,

        closeRightDrawer,

        setOnLeftClose,

      }}

    >

      {children}

    </DrawerContext.Provider>

  );

}

/* ============================================================
   HOOK
============================================================ */

export function useDrawer() {

  const context =
    useContext(
      DrawerContext,
    );

  if (!context) {

    throw new Error(

      "useDrawer must be used within DrawerProvider",

    );

  }

  return context;

}
