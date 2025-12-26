# Should be copied to ../instance folder to override some values
# WARNING: Be sure not to leave spaces around `=` because this
# Config file will be used both by Python and Bash

#### SERVER CONFIG ####
# Generate with `python -c 'import secrets; print(secrets.token_hex())'`
SECRET_KEY="dev"

# Front URL of the application (for QRCodes generation)
BASE_URL="http://localhost:5000"

# Port to run on
PORT="5000"

# Instance path ie. where are all the files + the database stored
# Keep in mind that this config option can only be loaded from default_config.py,
# as the custom config is stored in $INSTANCE_PATH/
INSTANCE_PATH="instance"

# Events to log
ENABLED_LOGS=["NEW_GROUPE", "NEW_ALBUM", "NEW_PARTITION", "NEW_USER", "PASSWORD_CHANGE", "DELETE_ACCOUNT", "SERVER_RESTART", "FAILED_LOGIN", "GOOGLE_ERROR"]

#### GOOGLE API CONFIG ####
# Google API key, with programmable search enabled
# You can create one at: https://developers.google.com/custom-search/v1/overview
GOOGLE_API_KEY=""

# Programmable search engine id
# You can obtain one at: https://programmablesearchengine.google.com/controlpanel/create
GOOGLE_SEARCH_ENGINE_ID=""

# Number of online queries a user can do (does not apply to admins)
MAX_ONLINE_QUERIES=3

#### APP CONFIG ####
# Disable registration of new users via /auth/register (they can still be added by root)
DISABLE_REGISTER=False

# Disable account deletion for users (still possible for admins)
DISABLE_ACCOUNT_DELETION=False

# Set this to True if you want local search to be across all albums (not just those the user belong to)
PRIVATE_SEARCH=False

# Session expiration, in days
MAX_AGE=31

# Available languages
LANGUAGES=['en', 'fr']

# Show Launch page
LAUNCH_PAGE=True

# Check if account is logged in before serving zipped album/groupe
ZIP_REQUIRE_LOGIN=True

