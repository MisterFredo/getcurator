"use client";

import {
  createContext,
  useContext,
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

  leftDrawer: DrawerSlot<LeftDrawerType>;

  rightDrawer: DrawerSlot<RightDrawerType>;

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

  closeLeftDrawer: () => void;

  closeRightDrawer: () => void;

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

        console.error(e);

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
  
    setRightDrawer({
  
      type,
  
      id,
  
      mode,
  
      payload,
  
    });
  
  }

  function closeRightDrawer() {

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
