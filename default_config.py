# Should be copied to ../instance folder to override some values
# WARNING: Be sure not to leave spaces around `=` because this
# Config file will be used both by Python and Bash

# Generate with `python -c 'import secrets; print(secrets.token_hex())'`
SECRET_KEY="dev"

# Port to run on
PORT="5000"

# Number of online queries an "normal user" can do
MAX_ONLINE_QUERIES=3

# Disable registration of new users via /auth/register (they can still be added by root)
DISABLE_REGISTER=False

# Disable account deletion for users (still possible for admins)
DISABLE_ACCOUNT_DELETION=False

# Set this to True if you want local search to be across all albums (not just those the user belong to)
PRIVATE_SEARCH=False

# Front URL of the application (for QRCodes generation)
BASE_URL="http://localhost:5000"

# Session expiration, in days
MAX_AGE=31

# Instance path ie. where are all the files + the database stored
# Keep in mind that this config option can only be loaded from default_config.py,
# as the custom config is stored in $INSTANCE_PATH/
INSTANCE_PATH="instance"

# Events to log
ENABLED_LOGS=["NEW_GROUPE", "NEW_ALBUM", "NEW_PARTITION", "NEW_USER", "PASSWORD_CHANGE", "DELETE_ACCOUNT", "SERVER_RESTART", "FAILED_LOGIN"]

# Available languages
LANGUAGES=['en', 'fr']

# Show Launch page
LAUNCH_PAGE=True

# Check if account is logged in before serving zipped album/groupe
ZIP_REQUIRE_LOGIN=True