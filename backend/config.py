# backend/config.py

import os

# ---------------------------------------------------------
# BigQuery configuration
# ---------------------------------------------------------
# Les variables sont définies dans Render.
#
# DEV
#   BQ_PROJECT = getcurator
#   BQ_DATASET = GETCURATOR_DEV
#
# PROD
#   BQ_PROJECT = getcurator
#   BQ_DATASET = GETCURATOR_PROD
#
# Secret :
#   GOOGLE_CREDENTIALS_FILE = /etc/secrets/bq.json
# ---------------------------------------------------------

BQ_PROJECT = os.getenv(
    "BQ_PROJECT",
    "getcurator",
)

BQ_DATASET = os.getenv(
    "BQ_DATASET",
    "GETCURATOR_PROD",
)

# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

ENV = os.getenv(
    "ENV",
    "local",
)
