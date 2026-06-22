"use client";

type Props = {

  open: boolean;

  digestName: string;
  setDigestName: (
    value: string
  ) => void;

  frequency: string;
  setFrequency: (
    value: string
  ) => void;

  onClose: () => void;

  onCreate: () => void;
};

export default function DigestCreateModal({

  open,

  digestName,
  setDigestName,

  frequency,
  setFrequency,

  onClose,
  onCreate,

}: Props) {

  if (!open) {
    return null;
  }

  return (

    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

      <div className="bg-white rounded-lg w-full max-w-md p-6 space-y-4">

        <h2 className="text-lg font-semibold">
          Create Digest
        </h2>

        <div>

          <label className="text-sm font-medium">
            Digest Name
          </label>

          <input
            value={digestName}
            onChange={(e) =>
              setDigestName(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2 mt-1"
          />

        </div>

        <div>

          <label className="text-sm font-medium">
            Frequency
          </label>

          <select
            value={frequency}
            onChange={(e) =>
              setFrequency(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2 mt-1"
          >

            <option value="WEEKLY">
              Weekly
            </option>

            <option value="MONTHLY">
              Monthly
            </option>

            <option value="QUARTERLY">
              Quarterly
            </option>

          </select>

        </div>

        <div className="flex justify-end gap-2">

          <button
            onClick={onClose}
            className="px-3 py-2 border rounded"
          >
            Cancel
          </button>

          <button
            onClick={onCreate}
            className="px-3 py-2 bg-black text-white rounded"
          >
            Create
          </button>

        </div>

      </div>

    </div>
  );
}
