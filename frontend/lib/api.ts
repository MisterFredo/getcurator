// frontend/lib/api.ts

const RAW_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://ratecard.onrender.com/api";

/* ========================================================= */

const BASE_URL = RAW_BASE_URL.replace(/\/+$/, "");

/* ========================================================= */

function getUserHeaders(): Record<string, string> {
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("user_id")
      : null;

  return userId ? { "x-user-id": userId } : {};
}

/* ========================================================= */

async function parseResponse(
  res: Response,
  path: string,
  errorLabel: string,
  requestBody?: unknown,
) {
  let json: any = null;

  try {
    json = await res.json();
  } catch {
    throw new Error(
      `Backend returned a non-JSON response (${res.status}).`
    );
  }

  if (!res.ok) {
    console.error(errorLabel, {
      status: res.status,
      path,
      ...(requestBody !== undefined ? { request: requestBody } : {}),
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
/* JSON REQUEST */
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
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
    credentials: "include",
  });

  return parseResponse(res, cleanPath, "❌ API ERROR", body);
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

  return parseResponse(res, cleanPath, "❌ API TEXT ERROR");
}

/* ========================================================= */
/* FORM DATA REQUEST — PDF STUDIO */
/* ========================================================= */

async function requestForm(
  method: string,
  path: string,
  body: FormData,
) {
  const cleanPath =
    path.startsWith("/") ? path : `/${path}`;

  const res = await fetch(`${BASE_URL}${cleanPath}`, {
    method,
    headers: {
      ...getUserHeaders(),
      // Do not set Content-Type: the browser supplies the multipart boundary.
    },
    body,
    cache: "no-store",
    credentials: "include",
  });

  return parseResponse(res, cleanPath, "❌ API FORM ERROR");
}

/* ========================================================= */

export const api = {
  get: (path: string) => request("GET", path),
  post: (path: string, body: any) => request("POST", path, body),
  postText: (path: string, body: string) => requestText("POST", path, body),
  postForm: (path: string, body: FormData) => requestForm("POST", path, body),
  put: (path: string, body: any) => request("PUT", path, body),
  delete: (path: string) => request("DELETE", path),
};
