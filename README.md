# Habit Tracker

A private, Habitify-inspired habit tracker with a daily overview, check-ins,
progress charts, and Google sign-in.

## Run locally

From this directory, create `.streamlit/secrets.toml` and configure the
credentials and database connection. Do not commit or share this file.

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "replace-with-a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[admin]
emails = ["authorized-person@example.com"]

[habits_connection]
DB_CONNECTION = "your-sqlite-cloud-connection-string"

[gemini]
api_key = "your-gemini-api-key"
```

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
For a published Streamlit Community Cloud app, also add the `[gemini]` section
to the app's **Settings > Secrets**; local secrets are not published with the app.
The Today page sends active habit names, descriptions, and today's progress to
Gemini only when you request suggestions. The user's email is not sent.

In Google Cloud Console, create a Web application OAuth client and add
`http://localhost:8501/oauth2callback` as an authorized redirect URI. For a
deployed app, change both the `redirect_uri` and the Google client's authorized
redirect URI to the deployed app's `/oauth2callback` URL. If the Google
consent screen is in testing mode, add each permitted account as a test user.

Only verified Google accounts listed in `[admin].emails` can access the app.
The app does not collect Google passwords. Existing password values in the
legacy `users` table are cleared for an account when it first signs in with
Google; new account records use an empty password field for compatibility with
the existing database schema.

For numeric habits, set a target for the selected date on the Daily check-in
page, then log amounts as you make progress. The daily target entered when
creating the habit is the default for each day, and can be overridden on the
Daily check-in page. Existing databases need these one-time migrations:

```sql
ALTER TABLE daily_tracking ADD COLUMN DAILY_GOAL REAL;
ALTER TABLE habit_list ADD COLUMN DEFAULT_DAILY_GOAL REAL;
```

Progress is accumulated in `COUNT_COMPLETED`; numeric check-ins count as
complete for streaks and daily totals when the amount reaches `DAILY_GOAL`.

Install dependencies and start Streamlit:

```powershell
python -m pip install -r requirements.txt
streamlit run Home.py
```
