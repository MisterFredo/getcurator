type Props = {
  selectedCount: number;
  onStore: () => void;
  onDismiss: () => void;
};

export default function DiscoveryActions({
  selectedCount,
  onStore,
  onDismiss,
}: Props) {

  return (

    <div className="flex gap-3">

      <button
        onClick={onStore}
        disabled={selectedCount === 0}
        className="bg-green-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        STOCKER ({selectedCount})
      </button>

      <button
        onClick={onDismiss}
        disabled={selectedCount === 0}
        className="bg-red-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        DISMISS ({selectedCount})
      </button>

    </div>

  );
}
