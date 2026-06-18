"use client";

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const VIDEO_URL =
  `${GCS_BASE_URL}/product/getcurator-tour-v1.mp4`;

export default function ProductTourPage() {

  return (

    <div className="max-w-6xl mx-auto">

      {/* HEADER */}

      <div className="mb-8">

        <h1
          className="
            text-3xl
            font-bold
            text-gray-900
          "
        >
          GetCurator Product Tour
        </h1>

        <p
          className="
            mt-2
            text-gray-600
            text-lg
          "
        >
          Discover how to monitor companies, topics, solutions and strategic
          signals with GetCurator. Watch the product tour below and book a
          personalized demo if you'd like to learn more.
        </p>

      </div>

      {/* VIDEO */}

      <div
        className="
          bg-white
          border
          rounded-xl
          overflow-hidden
          shadow-sm
        "
      >

        <video
          controls
          playsInline
          preload="metadata"
          className="
            w-full
            h-auto
            bg-black
          "
        >

          <source
            src={VIDEO_URL}
            type="video/mp4"
          />

          Your browser does not support video playback.

        </video>

      </div>

      {/* CTA */}

      <div
        className="
          mt-6
          flex
          justify-center
        "
      >

        <a
          href="https://calendly.com/martin-ratecard-events/30m"
          target="_blank"
          rel="noopener noreferrer"
          className="
            inline-flex
            items-center
            justify-center
            px-6
            py-3
            rounded-lg
            bg-emerald-600
            text-white
            font-medium
            hover:bg-emerald-700
            transition
          "
        >
          Book a Demo
        </a>

      </div>

      {/* MODULES */}

      <div
        className="
          mt-8
          grid
          gap-4
          md:grid-cols-4
        "
      >

        <div
          className="
            bg-white
            border
            rounded-lg
            p-4
          "
        >

          <div
            className="
              font-semibold
              text-gray-900
            "
          >
            Feed
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Follow the latest signals across your industries and markets.
          </div>

        </div>

        <div
          className="
            bg-white
            border
            rounded-lg
            p-4
          "
        >

          <div
            className="
              font-semibold
              text-gray-900
            "
          >
            Companies
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Track companies and understand how they evolve over time.
          </div>

        </div>

        <div
          className="
            bg-white
            border
            rounded-lg
            p-4
          "
        >

          <div
            className="
              font-semibold
              text-gray-900
            "
          >
            Topics
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Explore the themes and trends shaping your market.
          </div>

        </div>

        <div
          className="
            bg-white
            border
            rounded-lg
            p-4
          "
        >

          <div
            className="
              font-semibold
              text-gray-900
            "
          >
            Workspace
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Generate insights and structured analysis from selected content.
          </div>

        </div>

      </div>

    </div>

  );
}
