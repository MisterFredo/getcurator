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

    background: #F5F7FA;

    font-family: Arial, Helvetica, sans-serif;

    color: #222222;

}

table {

    border-collapse: collapse;

}

a {

    color: #315EFB;

    text-decoration: none;

}


/* ==========================================================
   TYPOGRAPHY
========================================================== */

h1 {

    margin: 0;

    font-size: 34px;

    font-weight: 700;

    line-height: 1.2;

}

h2 {

    margin: 0;

    font-size: 24px;

    font-weight: 700;

    line-height: 1.3;

}

h3 {

    margin: 28px 0 10px;

    font-size: 12px;

    font-weight: 700;

    letter-spacing: 1px;

    text-transform: uppercase;

    color: #6B7280;

}

p {

    margin: 0 0 16px;

    font-size: 15px;

    line-height: 1.7;

}


/* ==========================================================
   HEADER
========================================================== */

.header {

    padding: 18px 48px 14px;

    text-align: center;

    background: #FFFFFF;

}

.header h1 {

    margin: 0;

    font-size: 26px;

    font-weight: 700;

    line-height: 1.25;

    color: #111827;

}

.by-getcurator {

    font-weight: 500;

    color: #6B7280;

}

.digest-meta {

    margin: 8px 0 0;

    color: #315EFB;

    font-size: 11px;

    font-weight: 700;

    letter-spacing: 1px;

    text-transform: uppercase;

}

/* ==========================================================
   PROFILE
========================================================== */

.profile {

    padding: 0 48px 24px;

    background: #FFFFFF;

}

.profile-box {

    border: 1px solid #E5E7EB;

    border-radius: 14px;

    background: #FAFBFD;

    padding: 20px;

}

/* ==========================================================
   PROFILE HEADER
========================================================== */

.profile-header {

    display: flex;

    justify-content: space-between;

    align-items: flex-start;

    margin-bottom: 14px;

}

.profile-identity {

    flex: 1;

}

.profile-name {

    font-size: 20px;

    font-weight: 700;

    line-height: 1.2;

    color: #111827;

}

.profile-company {

    margin-top: 4px;

    font-size: 14px;

    color: #6B7280;

}

/* ==========================================================
   DESCRIPTION
========================================================== */

.profile-description {

    margin-bottom: 20px;

    color: #374151;

    font-size: 15px;

    line-height: 1.75;

}

/* ==========================================================
   EDIT PROFILE
========================================================== */

.profile-link {

    margin-left: 24px;

    white-space: nowrap;

}

.profile-link a {

    color: #315EFB;

    font-size: 12px;

    font-weight: 500;

    opacity: .75;

    text-decoration: none;

}

.profile-link a:hover {

    opacity: 1;

    text-decoration: underline;

}
/* ==========================================================
   BADGES
========================================================== */

.profile h3 {

    margin: 14px 0 6px;

}

.badge-list {

    margin-bottom: 8px;

}

.badge {

    margin: 0 6px 6px 0;

    padding: 6px 10px;

    font-size: 12px;

}
.badge-company {

    background: #F3E8FF;

    color: #7C3AED;

}

.badge-topic {

    background: #EEF4FF;

    color: #315EFB;

}

.badge-solution {

    background: #ECFDF3;

    color: #027A48;

}

.badge-keyword {

    background: #F3F4F6;

    color: #4B5563;

}


/* ==========================================================
   EXECUTIVE SUMMARY
========================================================== */

.summary {

    padding: 0 48px 22px;

    background: #FFFFFF;

}

.summary-box {

    padding: 18px 20px;

    border: 1px solid #E5E7EB;

    border-radius: 14px;

    background: linear-gradient(
        180deg,
        #FCFCFD 0%,
        #F8FAFC 100%
    );

}

.summary-pill {

    display: inline-block;

    margin-bottom: 16px;

    padding: 5px 12px;

    border-radius: 999px;

    background: #111827;

    color: #FFFFFF;

    font-size: 10px;

    font-weight: 700;

    letter-spacing: 1px;

    text-transform: uppercase;

}

.summary-content {

    font-size: 15px;

    line-height: 1.65;

    color: #374151;

}

.summary-content p {

    margin: 0 0 12px;

}

.summary-content p:last-child {

    margin-bottom: 0;

}

/* ==========================================================
   KEY POINTS
========================================================== */

.key-points {

    padding: 0 48px 22px;

}

/* ==========================================================
   STRATEGIC IMPLICATIONS
========================================================== */

.implications {

    padding: 0 48px 22px;

}

/* ==========================================================
   ANALYSIS CARDS
========================================================== */

.market-card {

    margin-bottom: 16px;

    padding: 18px 20px;

    border: 1px solid #E5E7EB;

    border-radius: 14px;

    background: #FFFFFF;

}

.market-card:last-child {

    margin-bottom: 0;

}

.market-card h3 {

    margin: 0 0 10px;

    font-size: 17px;

    font-weight: 700;

    line-height: 1.35;

    color: #111827;

    letter-spacing: normal;

    text-transform: none;

}

.market-card p {

    margin: 0;

    font-size: 15px;

    line-height: 1.65;

    color: #4B5563;

}

/* ==========================================================
   ARTICLES
========================================================== */

.articles {

    padding: 0 48px 36px;

}

/* ==========================================================
   SECTIONS
========================================================== */

.section {

    padding: 0 48px 22px;

    background: #FFFFFF;

}

.section h2 {

    margin: 0 0 12px;

}

.section-content {

    line-height: 1.7;

}

/* ==========================================================
   ARTICLE CARDS
========================================================== */

.card {

    margin-bottom: 14px;

    padding: 18px 20px;

    border: 1px solid #E5E7EB;

    border-radius: 14px;

    background: #FFFFFF;

}

.card:last-child {

    margin-bottom: 0;

}

.card h3 {

    margin: 0 0 6px;

    font-size: 18px;

    font-weight: 700;

    line-height: 1.3;

    color: #111827;

    text-transform: none;

    letter-spacing: normal;

}

.badge-list {

    margin-bottom: 8px;

}

.badge {

    margin: 0 4px 4px 0;

}

.meta {

    margin-bottom: 8px;

    font-size: 13px;

    color: #9CA3AF;

}

.card p {

    margin: 0 0 10px;

    font-size: 15px;

    line-height: 1.65;

    color: #4B5563;

}

.card p:last-of-type {

    margin-bottom: 0;

}

.cta {

    display: inline-block;

    margin-top: 6px;

    font-size: 11px;

    font-weight: 500;

}

/* ==========================================================
   FOOTER
========================================================== */

.footer {

    padding: 40px 48px;

    text-align: center;

    font-size: 12px;

    color: #9CA3AF;

    background: #FFFFFF;

}

"""

