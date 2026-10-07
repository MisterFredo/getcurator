// frontend/lib/api.ts

const RAW_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://ratecard.onrender.com/api";

/* ========================================================= */

const BASE_URL =
  RAW_BASE_URL.replace(/\/+$/, "");

/* ========================================================= */

function getUserHeaders(): Record<string, string> {
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("user_id")
      : null;

  return userId ? { "x-user-id": userId } : {};
}

/* ========================================================= */

async function request(
  method: string,
  path: string,
  body?: any,
) {
  const cleanPath =
    path.startsWith("/") ? path : `/${path}`;

  const res = await fetch(`${BASE_URL}${cleanPath}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...getUserHeaders(),
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
    credentials: "include",
  });

  let json: any = null;

  try {
    json = await res.json();
  } catch {
    throw new Error(
      `Backend returned a non-JSON response (${res.status}).`
    );
  }

  if (!res.ok) {
    console.error("❌ API ERROR", {
      status: res.status,
      path: cleanPath,
      request: body,
      response: json,
    });

    const message =
      typeof json?.detail === "string"
        ? json.detail
        : JSON.stringify(json, null, 2);

    throw new Error(message);
  }

  return json;
}

/* ========================================================= */
/* TEXT REQUEST */
/* ========================================================= */

async function requestText(
  method: string,
  path: string,
  body: string,
) {
  const cleanPath =
    path.startsWith("/") ? path : `/${path}`;

  const res = await fetch(`${BASE_URL}${cleanPath}`, {
    method,
    headers: {
      "Content-Type": "text/plain",
      ...getUserHeaders(),
    },
    body,
    cache: "no-store",
    credentials: "include",
  });

  let json: any = null;

  try {
    json = await res.json();
  } catch {
    throw new Error(
      `Backend returned a non-JSON response (${res.status}).`
    );
  }

  if (!res.ok) {
    console.error("❌ API TEXT ERROR", {
      status: res.status,
      path: cleanPath,
      response: json,
    });

    const message =
      typeof json?.detail === "string"
        ? json.detail
        : JSON.stringify(json, null, 2);

    throw new Error(message);
  }

  return json;
}

/* ========================================================= */

export const api = {
  get: (path: string) => request("GET", path),
  post: (path: string, body: any) => request("POST", path, body),
  postText: (path: string, body: string) => requestText("POST", path, body),
  put: (path: string, body: any) => request("PUT", path, body),
  delete: (path: string) => request("DELETE", path),
};
