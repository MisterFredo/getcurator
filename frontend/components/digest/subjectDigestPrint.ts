export function subjectReportBasename(
  profileName: string,
  periodStart: string,
  periodEnd: string,
  language?: string,
) {
  const profile = profileName.normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[œŒ]/g, value => value === "œ" ? "oe" : "OE")
    .replace(/[^A-Za-z0-9]+/g, "-")
    .slice(0, 100)
    .replace(/^-+|-+$/g, "");
  const title = profile ? "Digest-Sujets-" + profile : "Digest-Sujets";
  const lang = /^fr(?:$|[-_])/i.test(language?.trim() ?? "") ? "FR" : "EN";
  return `GetCurator_${title}_${periodStart}_to_${periodEnd}_${lang}_Report`;
}

export function subjectPrintHtml(content: string, title: string) {
  const safeTitle = title.replace(/[<&>]/g, character => (
    character === "<" ? "&lt;" : character === ">" ? "&gt;" : "&amp;"
  ));
  return `<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>${safeTitle}</title>
<style>
  @page { size: A4; margin: 15mm 16mm 16mm; }
  * { box-sizing: border-box; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  body { margin: 0; color: #172530; font: 10.5pt/1.48 Arial, sans-serif; overflow-wrap: anywhere; }
  header { border-top: 5px solid #143642; border-bottom: 1px solid #cbd8dc; padding: 12pt 0; margin-bottom: 14pt; break-inside: avoid; }
  header p { color: #405962; margin: 0; }
  header p:first-child { font-size: 8pt; letter-spacing: .075em; text-transform: uppercase; }
  h2 { color: #143642; font-size: 22pt; line-height: 1.13; margin: 6pt 0; }
  h3 { color: #143642; font-size: 10pt; letter-spacing: .05em; text-transform: uppercase; margin: 15pt 0 7pt; }
  h4 { color: #143642; font-size: 16pt; line-height: 1.23; margin: 0 0 7pt; }
  h2, h3, h4, .supporting-title { break-after: avoid; }
  p { margin: 0 0 7pt; orphans: 2; widows: 2; }
  section > article { border-top: 1px solid #dbe4e7; padding-top: 9pt; margin-bottom: 13pt; }
  [data-digest-brief] { background: #edf4f4; border-left: 3px solid #143642; padding: 9pt 11pt 3pt; margin-bottom: 14pt; }
  [data-digest-brief] h3 { margin-top: 0; font-size: 13pt; text-transform: none; }
  [data-digest-badges] { margin: 0 0 7pt; }
  [data-digest-badges] span { display: inline-block; border-radius: 9pt; padding: 1pt 6pt; margin: 0 3pt 3pt 0; font-size: 8pt; }
  [data-digest-why] { background: #f4f7f8; border-left: 2px solid #789da4; padding: 5pt 8pt; }
  .supporting-title { color: #405962; font-weight: bold; font-size: 9pt; margin: 8pt 0 3pt; }
  ul { padding: 0; margin: 0; list-style: none; }
  li { border-top: 1px solid #e5ebed; padding: 3pt 0; break-inside: avoid; font-size: 8.75pt; }
  a { color: #15566c; text-decoration: underline; }
</style>
<body>${content}</body>
</html>`;
}

export function printSubjectDigest(source: HTMLElement, title: string) {
  const clone = source.cloneNode(true) as HTMLElement;
  clone.querySelectorAll("details").forEach(details => {
    const block = document.createElement("div");
    const heading = document.createElement("p");
    heading.className = "supporting-title";
    heading.textContent = details.querySelector("summary")?.textContent?.trim() ?? "Supporting content";
    block.append(heading);
    for (const child of Array.from(details.children)) {
      if (child.tagName !== "SUMMARY") block.append(child);
    }
    details.replaceWith(block);
  });
  const frame = document.createElement("iframe");
  frame.setAttribute("aria-hidden", "true");
  frame.tabIndex = -1;
  frame.style.cssText = "position:fixed;width:1px;height:1px;left:-10000px;top:0;border:0";
  frame.onload = () => {
    const view = frame.contentWindow;
    if (!view) {
      frame.remove();
      return;
    }
    // Some browsers use the parent page title for an iframe's PDF filename.
    const previousTitle = document.title;
    const cleanup = () => {
      view.removeEventListener("afterprint", cleanup);
      window.removeEventListener("afterprint", cleanup);
      if (document.title === title) document.title = previousTitle;
      frame.remove();
    };
    view.addEventListener("afterprint", cleanup);
    window.addEventListener("afterprint", cleanup);
    document.title = title;
    try {
      view.focus();
      view.print();
    } catch (error) {
      cleanup();
      throw error;
    }
  };
  frame.srcdoc = subjectPrintHtml(clone.outerHTML, title);
  document.body.append(frame);
}
