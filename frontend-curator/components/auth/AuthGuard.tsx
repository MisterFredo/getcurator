"use client";

import {
  useEffect,
} from "react";

import {
  useRouter,
  usePathname,
} from "next/navigation";

import {
  useUser,
} from "@/hooks/useUser";

import {
  api,
} from "@/lib/api";


const SESSION_ID_KEY =
  "getcurator_session_id";

const SESSION_REGISTERED_KEY =
  "getcurator_session_registered";


/* =========================================================
   SESSION ID
========================================================= */

function getOrCreateSessionId() {

  const existingSessionId =
    sessionStorage.getItem(
      SESSION_ID_KEY
    );

  if (existingSessionId) {
    return existingSessionId;
  }

  const sessionId =
    crypto.randomUUID();

  sessionStorage.setItem(
    SESSION_ID_KEY,
    sessionId
  );

  return sessionId;
}


/* =========================================================
   AUTH GUARD
========================================================= */

export default function AuthGuard({
  children,
}: {
  children: React.ReactNode;
}) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    user,
    loading,
  } = useUser();


  /* =======================================================
     PUBLIC ROUTES
  ======================================================= */

  const isPublic =
    pathname === "/"
    || pathname.startsWith(
      "/login"
    );


  /* =======================================================
     REDIRECT
  ======================================================= */

  useEffect(() => {

    if (
      loading
      || !user
      || pathname.startsWith("/login")
    ) {
      return;
    }
  
    const alreadyRegistered =
      sessionStorage.getItem(
        SESSION_REGISTERED_KEY
      );
  
    if (alreadyRegistered) {
      return;
    }
  
    const sessionId =
      getOrCreateSessionId();
  
    /*
     * Positionné avant l'appel pour empêcher
     * plusieurs effets React simultanés.
     */
    sessionStorage.setItem(
      SESSION_REGISTERED_KEY,
      "true"
    );
  
    async function registerSession() {
  
      try {
  
        await api.post(
          "/user/access/session",
          {
            session_id: sessionId,
          }
        );
  
      } catch (error) {
  
        /*
         * On autorise une nouvelle tentative
         * si l'enregistrement a échoué.
         */
        sessionStorage.removeItem(
          SESSION_REGISTERED_KEY
        );
  
        console.error(
          "Unable to register user session",
          error
        );
  
      }
  
    }
  
    registerSession();
  
  }, [
    user,
    loading,
    pathname,
  ]);


  /* =======================================================
     REGISTER AUTHENTICATED SESSION
  ======================================================= */

  useEffect(() => {

    if (
      loading
      || !user
    ) {
      return;
    }

    const userId =
      localStorage.getItem(
        "user_id"
      );

    if (!userId) {
      return;
    }

    const sessionId =
      getOrCreateSessionId();

    const registrationKey =
      `${userId}:${sessionId}`;

    const registeredSession =
      sessionStorage.getItem(
        SESSION_REGISTERED_KEY
      );

    if (
      registeredSession
      === registrationKey
    ) {
      return;
    }

    async function registerSession() {

      try {

        await api.post(
          "/user/access/session",
          {
            session_id: sessionId,
          }
        );

        sessionStorage.setItem(
          SESSION_REGISTERED_KEY,
          registrationKey
        );

      } catch (error) {

        /*
         * Le tracking ne doit pas empêcher
         * l'utilisation de GetCurator.
         */

        console.error(
          "Unable to register user session",
          error
        );

      }

    }

    registerSession();

  }, [
    user,
    loading,
  ]);


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (

      <div className="
        min-h-screen
        flex
        items-center
        justify-center
        text-sm
        text-gray-500
      ">
        Chargement…
      </div>

    );

  }


  /* =======================================================
     PUBLIC
  ======================================================= */

  if (isPublic) {
    return <>{children}</>;
  }


  /* =======================================================
     NOT AUTHENTICATED
  ======================================================= */

  if (!user) {

    return (

      <div className="
        min-h-screen
        flex
        items-center
        justify-center
        text-sm
        text-gray-500
      ">
        Redirection…
      </div>

    );

  }


  /* =======================================================
     AUTHENTICATED
  ======================================================= */

  return <>{children}</>;
}
