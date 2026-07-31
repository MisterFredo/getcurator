# backend/core/digest/html_styles.py

# ============================================================
# DIGEST EMAIL STYLES
# ============================================================

DIGEST_EMAIL_STYLES = """

/* ==========================================================
   GLOBAL
========================================================== */

body {

    margin: 0;

    padding: 0;

    background: #f5f7fa;

    font-family: Arial, Helvetica, sans-serif;

    color: #222222;

}

table {

    border-collapse: collapse;

}

a {

    color: #0057ff;

    text-decoration: none;

}


/* ==========================================================
   TYPOGRAPHY
========================================================== */

h1 {

    margin: 0;

    font-size: 32px;

    font-weight: 700;

    line-height: 1.2;

}

h2 {

    margin: 0 0 16px 0;

    font-size: 24px;

    font-weight: 700;

}

h3 {

    margin: 0 0 8px 0;

    font-size: 18px;

    font-weight: 600;

}

p {

    margin: 0 0 16px 0;

    line-height: 1.6;

    font-size: 15px;

}


/* ==========================================================
   HEADER
========================================================== */

.header {

    padding: 48px 56px;

    text-align: center;

    border-bottom: 1px solid #E5E7EB;

}

.digest-type {

    display: inline-block;

    margin-bottom: 18px;

    padding: 6px 12px;

    border-radius: 999px;

    background: #EEF4FF;

    color: #315EFB;

    font-size: 11px;

    font-weight: 700;

    letter-spacing: 1.2px;

    text-transform: uppercase;

}

.header h1 {

    margin: 0;

    font-size: 34px;

    font-weight: 700;

    line-height: 1.2;

}

.reader-name {

    margin: 22px 0 6px;

    font-size: 22px;

    font-weight: 600;

}

.reader-role {

    margin: 0;

    color: #6B7280;

    font-size: 15px;

}

.period {

    margin-top: 26px;

    font-size: 15px;

    color: #374151;

}

.prepared {

    margin-top: 8px;

    color: #9CA3AF;

    font-size: 13px;

}
/* ==========================================================
   PROFILE
========================================================== */

.profile {

    background: #ffffff;

    padding: 24px 48px 40px 48px;

}

.profile-description {

    color: #666666;

    margin-bottom: 24px;

}

/* ==========================================================
   BADGES
========================================================== */

.badge-list {

    margin-bottom: 24px;

}

.badge {

    display: inline-block;

    margin: 0 8px 8px 0;

    padding: 6px 12px;

    border-radius: 999px;

    background: #eef3ff;

    color: #0057ff;

    font-size: 13px;

    font-weight: 600;

    line-height: 1;

}


/* ==========================================================
   SECTIONS
========================================================== */

.section {

    background: #ffffff;

    padding: 0 48px 40px 48px;

}

.section-content {

    margin-bottom: 24px;

}


/* ==========================================================
   CARDS
========================================================== */

.card {

    border: 1px solid #e8e8e8;

    border-radius: 10px;

    padding: 24px;

    margin-top: 24px;

}

.meta {

    font-size: 13px;

    color: #888888;

}

.cta {

    display: inline-block;

    margin-top: 8px;

    font-size: 14px;

    font-weight: 600;

}


/* ==========================================================
   FOOTER
========================================================== */

.footer {

    padding: 40px;

    text-align: center;

    font-size: 12px;

    color: #888888;

}
"""
