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