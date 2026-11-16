import streamlit as st


def _missing_google_settings() -> list[str]:
    auth_settings = st.secrets.get("auth", {})
    required_settings = {
        "auth.redirect_uri": auth_settings.get("redirect_uri"),
        "auth.cookie_secret": auth_settings.get("cookie_secret"),
        "auth.google.client_id": auth_settings.get("client_id"),
        "auth.google.client_secret": auth_settings.get("client_secret"),
        "auth.google.server_metadata_url": auth_settings.get(
            "server_metadata_url"
        ),
    }
    return [name for name, value in required_settings.items() if not value]


def require_user() -> str:
    if not st.user.is_logged_in:
        st.title("Build a routine that feels like yours")
        st.write(
            "Keep your habits, daily check-ins, and progress in one calm place."
        )
        st.caption("Sign in with an authorized Google account to continue.")

        missing_settings = _missing_google_settings()
        if missing_settings:
            st.error(
                "Google sign-in is not configured. Add these values to "
                ".streamlit/secrets.toml: "
                + ", ".join(missing_settings)
            )
        elif st.button("Continue with Google", type="primary"):
            st.login("google")
            st.stop()
        st.stop()

    email = str(getattr(st.user, "email", "")).strip().lower()
    email_verified = getattr(st.user, "email_verified", False)
    access_settings = st.secrets.get("admin", {})
    configured_emails = access_settings.get("emails", [])

    if not isinstance(configured_emails, list):
        st.error("The [access] emails setting must be a list.")
        st.stop()

    allowed_emails = {
        allowed.strip().lower()
        for allowed in configured_emails
        if isinstance(allowed, str) and allowed.strip()
    }
    if not email or not email_verified or email not in allowed_emails:
        st.error(
            "This verified Google account is not authorized to use this app."
        )
        if not allowed_emails:
            st.info("Add permitted addresses to the emails list in [access].")
        if st.button("Sign out"):
            st.logout()
            st.stop()
        st.stop()

    if st.session_state.get("provisioned_email") != email:
        from py.habits import ensure_user

        ensure_user(email)
        st.session_state["provisioned_email"] = email

    st.sidebar.caption(f"Signed in as {email}")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("provisioned_email", None)
        st.logout()
        st.stop()
    return email
