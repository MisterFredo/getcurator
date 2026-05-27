export function EmailLayout(content: string) {
  return `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<base target="_blank" />

<style>
  body, table, td, div, p {
    font-family: Arial, Helvetica, sans-serif !important;
  }

  @media only screen and (max-width: 600px) {

    .container {
      width: 100% !important;
      max-width: 100% !important;
    }

    .mobile-padding {
      padding-left: 16px !important;
      padding-right: 16px !important;
    }

    .stack-column {
      display: block !important;
      width: 100% !important;
      max-width: 100% !important;
      padding-right: 0 !important;
    }

    .mobile-center {
      text-align: center !important;
    }

    .responsive-img {
      height: auto !important;
    }

    .logo-img {
      max-width: 140px !important;
      height: auto !important;
    }

    .thumb-img {
      max-width: 260px !important;
      height: auto !important;
    }
  }
</style>
</head>

<body style="
  margin:0;
  padding:0;
  background:#F3F4F6;
  font-family:Arial,Helvetica,sans-serif;
">

  <!-- WRAPPER -->
  <table width="100%" cellpadding="0" cellspacing="0" role="presentation"
    style="background:#F3F4F6;"
  >
    <tr>
      <td align="center">

        <!-- SPACER TOP -->
        <table width="100%" role="presentation">
          <tr><td height="24"></td></tr>
        </table>

        <!-- MAIN CARD -->
        <table
          width="720"
          cellpadding="0"
          cellspacing="0"
          role="presentation"
          class="container"
          style="
            width:100%;
            max-width:720px;
            margin:0 auto;
            background:#FFFFFF;
            border-radius:8px;
            overflow:hidden;
            box-shadow:0 1px 2px rgba(0,0,0,0.04);
          "
        >

          <!-- CONTENT WRAPPER -->
          <tr>
            <td style="padding:0 32px;">

              <!-- INNER WRAPPER -->
              <table 
                width="100%" 
                cellpadding="0" 
                cellspacing="0" 
                role="presentation"
              >

                ${content}

              </table>

            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="
              padding:32px;
              border-top:1px solid #E5E7EB;
              font-size:12px;
              color:#9CA3AF;
              line-height:1.5;
              text-align:left;
            ">
              © Ratecard<br/>
              Lecture stratégique du marché
            </td>
          </tr>

        </table>

        <!-- SPACER BOTTOM -->
        <table width="100%" role="presentation">
          <tr><td height="24"></td></tr>
        </table>

      </td>
    </tr>
  </table>

</body>
</html>
`;
}
