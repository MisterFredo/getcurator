"use client";

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const VIDEO_URL =
  `${GCS_BASE_URL}/product/getcurator-tour-v2.mp4`;

export default function ProductTourPage() {

  return (

    <div className="w-full">

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
          Discover how GetCurator transforms industry signals into personalized
          intelligence through curated content, weekly digests, specialized
          experts and contextual conversations. Watch the product tour below
          and book a personalized demo to explore how GetCurator can support
          your decisions.
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
          max-w-4xl
          mx-auto
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
          sm:grid-cols-2
          lg:grid-cols-5
        "
      >

        {/* PERSONALIZED HOME */}

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
            Personalized Home
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Follow the signals most relevant to your priorities and markets.
          </div>

        </div>

        {/* DIGESTS */}

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
            Weekly Digests
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Connect recent developments and identify emerging strategic
            patterns.
          </div>

        </div>

        {/* EXPERTS */}

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
            Experts
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Build your own intelligence team around companies, markets and
            competitive dynamics.
          </div>

        </div>

        {/* CONVERSATIONS */}

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
            Conversations
          </div>

          <div
            className="
              mt-2
              text-sm
              text-gray-600
            "
          >
            Ask questions and receive contextualized answers grounded in
            accumulated knowledge.
          </div>

        </div>

        {/* WORKSPACE */}

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
            Turn selected signals into focused insights and structured
            analysis.
          </div>

        </div>

      </div>

    </div>

  );
}
