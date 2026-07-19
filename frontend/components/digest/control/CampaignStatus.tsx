"use client";

type Props = {
  status:
    | "NOT_GENERATED"
    | "GENERATING"
    | "READY"
    | "SENDING"
    | "SENT"
    | "FAILED";

  generatedUsers?: number;

  totalUsers?: number;

  sentUsers?: number;

  totalToSend?: number;
};

export default function CampaignStatus({
  status,
  generatedUsers = 0,
  totalUsers = 0,
  sentUsers = 0,
  totalToSend = 0,
}: Props) {

  function renderStatus() {

    switch (status) {

      case "NOT_GENERATED":

        return (
          <>
            <div className="text-lg font-semibold">
              Campaign not generated
            </div>

            <div className="text-sm text-gray-500">
              Ready to generate this week's digests.
            </div>
          </>
        );

      case "GENERATING":

        return (
          <>
            <div className="text-lg font-semibold">
              Generating campaign...
            </div>

            <div className="text-sm text-gray-500">
              {generatedUsers} / {totalUsers} users processed
            </div>
          </>
        );

      case "READY":

        return (
          <>
            <div className="text-lg font-semibold text-green-700">
              Campaign ready
            </div>

            <div className="text-sm text-gray-500">
              All digests have been generated.
            </div>
          </>
        );

      case "SENDING":

        return (
          <>
            <div className="text-lg font-semibold">
              Sending campaign...
            </div>

            <div className="text-sm text-gray-500">
              {sentUsers} / {totalToSend} emails sent
            </div>
          </>
        );

      case "SENT":

        return (
          <>
            <div className="text-lg font-semibold text-green-700">
              Campaign completed
            </div>

            <div className="text-sm text-gray-500">
              All digests have been delivered.
            </div>
          </>
        );

      case "FAILED":

        return (
          <>
            <div className="text-lg font-semibold text-red-600">
              Campaign failed
            </div>

            <div className="text-sm text-gray-500">
              Some digests could not be generated or sent.
            </div>
          </>
        );

    }

  }

  return (

    <div className="bg-white border rounded-xl p-6">

      {renderStatus()}

    </div>

  );

}
