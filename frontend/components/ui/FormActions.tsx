"use client";

type Props = {
  saving: boolean;

  saveLabel?: string;

  cancelLabel?: string;

  showDelete?: boolean;

  deleteLabel?: string;

  onSave: () => void;

  onCancel?: () => void;

  onDelete?: () => void;
};

export default function ProfileActionsBar({
  saving,

  saveLabel = "Save",

  cancelLabel = "Cancel",

  deleteLabel = "Delete",

  showDelete = false,

  onSave,

  onCancel,

  onDelete,
}: Props) {

  return (

    <div
      className="
        flex
        items-center
        justify-between
        border-t
        pt-6
      "
    >

      {/* ===================================================== */}
      {/* LEFT */}
      {/* ===================================================== */}

      <div className="flex gap-3">

        {showDelete && onDelete && (

          <button
            type="button"
            onClick={onDelete}
            className="
              rounded-lg
              border
              border-red-300
              px-4
              py-2
              text-red-600
              transition
              hover:bg-red-50
            "
          >
            {deleteLabel}
          </button>

        )}

      </div>

      {/* ===================================================== */}
      {/* RIGHT */}
      {/* ===================================================== */}

      <div className="flex gap-3">

        {onCancel && (

          <button
            type="button"
            onClick={onCancel}
            className="
              rounded-lg
              border
              px-4
              py-2
              transition
              hover:bg-gray-50
            "
          >
            {cancelLabel}
          </button>

        )}

        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="
            rounded-lg
            bg-ratecard-blue
            px-6
            py-2
            text-white
            transition
            hover:opacity-90
            disabled:opacity-50
          "
        >

          {saving
            ? "Saving..."
            : saveLabel}

        </button>

      </div>

    </div>

  );

}
