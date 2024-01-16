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

# Front URL of the application (for QRCodes generation)
BASE_URL="http://localhost:5000"

# Session expiration, in days
MAX_AGE=31

# Instance path ie. where are all the files + the database stored
# Keep in mind that this config option can only be loaded from default_config.py,
# as the custom config is stored in $INSTANCE_PATH/
INSTANCE_PATH="instance"
