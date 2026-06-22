"use client";

type Props = {

  digestName: string;

  setDigestName: (
    value: string
  ) => void;

  lastSentAt?: string | null;

  onSave?: () => void;

  isExistingDigest?: boolean;
};

export default function DigestStudioHeader({

  digestName,

  setDigestName,

  lastSentAt,

  onSave,

  isExistingDigest,
}: Props) {

  return (

    <div className="flex items-center justify-between">

      <div>

        <input
          value={digestName}
          onChange={(e) =>
            setDigestName(
              e.target.value
            )
          }
          placeholder="Digest Name"
          className="
            text-lg
            font-semibold
            border-0
            p-0
            bg-transparent
            focus:outline-none
          "
        />

        <div className="text-sm text-gray-500 mt-1">

          Digest Studio

        </div>

      </div>

      <div className="flex items-center gap-3">

        {lastSentAt && (

          <div className="text-right">

            <div className="text-xs text-gray-400">

              Last sent

            </div>

            <div className="text-sm">

              {new Date(
                lastSentAt
              ).toLocaleDateString()}
            </div>

          </div>

        )}

        {isExistingDigest && (

          <button
            onClick={onSave}
            className="
              px-3
              py-2
              rounded
              bg-black
              text-white
              text-xs
            "
          >
            Save Digest
          </button>

        )}

      </div>

    </div>
  );
}
