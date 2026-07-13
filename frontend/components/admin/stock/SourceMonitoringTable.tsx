type Source = {
  SOURCE_ID: string;
  SOURCE_NAME: string;
  LAST_ARTICLE_DATE?: string;
  LAST_ARTICLE_URL?: string;
  LAST_ARTICLE_TITLE?: string;
  LAST_IMPORT_AT?: string;
  NB_IMPORTED_7D?: number;

  // 🔥 NEW
  PRIMARY_COMPANY_NAME?: string;
};

export default function SourceMonitoringTable({
  sources,
}: {
  sources: Source[];
}) {
  return (
    <table className="w-full text-sm">
      <thead className="bg-gray-50 border-b">
        <tr>
          <th className="text-left p-3">Source</th>

          {/* 🔥 NEW */}
          <th className="text-left p-3">Type</th>

          {/* 🔥 NEW */}
          <th className="text-left p-3">
            Primary company
          </th>

          <th className="text-left p-3">Last article</th>
          <th className="text-left p-3">Date</th>
          <th className="text-left p-3">Imports (7j)</th>
          <th className="text-left p-3">Last import</th>
        </tr>
      </thead>

      <tbody>
        {sources.map((s) => (
          <tr
            key={s.SOURCE_ID}
            className="border-b hover:bg-gray-50"
          >
            <td className="p-3 font-medium">
              {s.SOURCE_NAME}
            </td>

            {/* 🔥 NEW */}
            <td className="p-3">
              {s.PRIMARY_COMPANY_NAME || "-"}
            </td>

            <td className="p-3">
              {s.LAST_ARTICLE_URL ? (
                <a
                  href={s.LAST_ARTICLE_URL}
                  target="_blank"
                  className="text-blue-600 hover:underline"
                >
                  {s.LAST_ARTICLE_TITLE}
                </a>
              ) : (
                s.LAST_ARTICLE_TITLE
              )}
            </td>

            <td className="p-3">
              {s.LAST_ARTICLE_DATE}
            </td>

            <td className="p-3">
              {s.NB_IMPORTED_7D || 0}
            </td>

            <td className="p-3 text-gray-500 text-xs">
              {s.LAST_IMPORT_AT}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
