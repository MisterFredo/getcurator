export function EmailEditorialBlockGmail(
  html: string
) {

  if (!html) {
    return "";
  }

  return `
<tr>
<td style="
  padding:32px 32px 36px 32px;
  border-bottom:1px solid #F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  <div style="
    font-size:12px;
    text-transform:uppercase;
    letter-spacing:0.12em;
    color:#9CA3AF;
    margin-bottom:18px;
    font-weight:600;
  ">
    Points à retenir
  </div>

  <div style="
    background:#FAFAFA;
    border:1px solid #F3F4F6;
    border-radius:16px;
    padding:22px 24px;
  ">

    <div style="
      font-size:15px;
      line-height:1.8;
      color:#111827;
      max-width:620px;
    ">
      ${html}
    </div>

  </div>

</td>
</tr>
`;
}
