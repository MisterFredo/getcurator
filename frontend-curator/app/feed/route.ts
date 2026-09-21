import {
  NextRequest,
  NextResponse,
} from "next/server";

/* =========================================================
   LEGACY FEED REDIRECT
========================================================= */

export function GET(
  request: NextRequest,
) {

  const query =
    request.nextUrl.searchParams
      .toString();

  /*
   * Use a relative Location header.
   *
   * This preserves the public domain used
   * by the browser and avoids Render's
   * internal localhost:3001 address.
   */

  const location =
    query
      ? `/?${query}`
      : "/";

  return new NextResponse(
    null,
    {
      status:
        307,

      headers: {
        Location:
          location,
      },
    },
  );

}
