// frontend/lib/api.ts

const RAW_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://ratecard.onrender.com/api";

/* ========================================================= */

const BASE_URL =
  RAW_BASE_URL.replace(/\/+$/, "");

/* ========================================================= */

async function request(
  method: string,
  path: string,
  body?: any,
) {

  const cleanPath =
    path.startsWith("/")
      ? path
      : `/${path}`;

  const res = await fetch(

    `${BASE_URL}${cleanPath}`,

    {
      method,

      headers: {
        "Content-Type": "application/json",
      },

      body:
        body
          ? JSON.stringify(body)
          : undefined,

      cache: "no-store",

      credentials: "include",
    }

  );

  let json: any = null;

  try {

    json = await res.json();

  } catch {

    throw new Error(
      `Backend returned a non-JSON response (${res.status}).`
    );

  }

  if (!res.ok) {

    console.error(
      "❌ API ERROR",
      {
        status: res.status,
        path: cleanPath,
        request: body,
        response: json,
      }
    );

    const message =
      typeof json?.detail === "string"

        ? json.detail

        : JSON.stringify(
            json,
            null,
            2
          );

    throw new Error(message);

  }

  return json;

}

/* ========================================================= */

export const api = {

  get: (path: string) =>
    request("GET", path),

  post: (
    path: string,
    body: any,
  ) =>
    request("POST", path, body),

  put: (
    path: string,
    body: any,
  ) =>
    request("PUT", path, body),

  delete: (path: string) =>
    request("DELETE", path),

};
