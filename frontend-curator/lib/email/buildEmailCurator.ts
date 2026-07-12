export function buildEmailCurator({ news, analyses }: any) {

  let html = `
    <div style="font-family:Arial, sans-serif; max-width:680px; margin:auto;">
      <h2 style="font-size:18px; margin-bottom:20px;">
        📊 Veille personnalisée
      </h2>
  `;

  // =========================
  // ANALYSES
  // =========================
  if (analyses.length > 0) {
    html += `<h3 style="margin-top:20px;">📈 Analyses</h3>`;

    analyses.forEach((a: any) => {
      html += `
        <div style="margin-bottom:16px;">
          <div style="font-weight:600;">
            ${a.title}
          </div>

          <div style="margin:6px 0;">
            ${renderBadges(a)}
          </div>

          <div style="color:#555;">
            ${a.excerpt || ""}
          </div>
        </div>
      `;
    });
  }

  html += `</div>`;

  return html;
}

/* ========================================================= */

function renderBadges(item: any) {

  const badges: string[] = [];

  item.companies?.forEach((c: any) => {
    if (c.name) {
      badges.push(`
        <span style="
          background:#eef2ff;
          color:#3730a3;
          padding:2px 6px;
          border-radius:6px;
          font-size:11px;
          margin-right:4px;
        ">
          ${c.name}
        </span>
      `);
    }
  });

  item.topics?.forEach((t: any) => {
    if (t.label) {
      badges.push(`
        <span style="
          background:#f3f4f6;
          color:#374151;
          padding:2px 6px;
          border-radius:6px;
          font-size:11px;
          margin-right:4px;
        ">
          ${t.label}
        </span>
      `);
    }
  });

  return badges.join("");
}
