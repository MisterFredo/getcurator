import {
  NextRequest,
  NextResponse,
} from "next/server";

export function GET(
  request: NextRequest,
) {

  const target =
    new URL(
      "/",
      request.url,
    );

  request.nextUrl.searchParams.forEach(
    (
      value,
      key,
    ) => {

      target.searchParams.set(
        key,
        value,
      );

    },
  );

  return NextResponse.redirect(
    target,
    307,
  );

}
