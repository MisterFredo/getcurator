"use client";

type NumberItem = {
  id: string;
  label?: string;
  value?: number;
  unit?: string;
  zone?: string;
  period?: string;
  actor?: string;
};

type Props = {
  item: NumberItem;
  selected: boolean;
  onClick: () => void;
};

export default function NumberRow({ item, selected, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className={`
        border rounded p-3 cursor-pointer transition
        ${selected ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}
      `}
    >
      <div className="text-sm font-medium">
        {item.label}
      </div>

      <div className="text-xs text-gray-500">
        {item.value} {item.unit}
        {item.zone && ` • ${item.zone}`}
        {item.period && ` • ${item.period}`}
      </div>

      {item.actor && (
        <div className="text-xs text-gray-400">
          {item.actor}
        </div>
      )}
    </div>
  );
}
