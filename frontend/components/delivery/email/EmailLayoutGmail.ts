export function EmailLayoutGmail(content: string) {
  return `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />

<style>
  body, table, td, div, p {
    font-family: Arial, Helvetica, sans-serif !important;
  }
</style>

</head>

<body style="
  margin:0;
  padding:0;
  background:#F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
    style="
      background:#F3F4F6;
      font-family:Arial,Helvetica,sans-serif;
    "
  >
    <tr>
      <td align="center" style="font-family:Arial,Helvetica,sans-serif;">

        <!-- MAIN CONTAINER -->
        <table
          width="720"
          cellpadding="0"
          cellspacing="0"
          role="presentation"
          style="
            width:100%;
            max-width:720px;
            background:#FFFFFF;
            font-family:Arial,Helvetica,sans-serif;
          "
        >

          <!-- CONTENT WRAPPER -->
          <tr>
            <td style="
              padding:0 24px;
              font-family:Arial,Helvetica,sans-serif;
              color:#111827;
            ">

              <!-- 🔥 INNER WRAPPER (CRITICAL) -->
              <table 
                width="100%" 
                cellpadding="0" 
                cellspacing="0" 
                role="presentation"
                style="font-family:Arial,Helvetica,sans-serif;"
              >

                ${content}

              </table>

            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="
              padding:36px 24px 26px 24px;
              font-size:12px;
              color:#9CA3AF;
              line-height:1.5;
              font-family:Arial,Helvetica,sans-serif;
            ">
              © Ratecard – Lecture stratégique du marché
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
`;
}
