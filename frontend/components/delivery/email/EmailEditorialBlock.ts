export function EmailEditorialBlock(html: string) {
  if (!html) return "";

  return `
<tr>
<td style="
  padding:24px 32px;
  border-bottom:1px solid #F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  <div style="
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:0.14em;
    color:#9CA3AF;
    margin-bottom:10px;
    font-weight:600;
  ">
    Editorial
  </div>

  <div style="
    font-size:15px;
    line-height:1.65;
    color:#111827;
    max-width:560px;
  ">
    ${html}
  </div>

</td>
</tr>
`;
}
