import streamlit as st
from loguru import logger

from open_notebook.domain.models import Settings
from open_notebook.exceptions import ConfigurationError


def show_settings_page():
    """Display the application settings page."""
    st.title("⚙️ Settings")
    
    settings = Settings.load()
    
    st.subheader("Database Configuration")
    with st.form("db_settings"):
        surrealdb_url = st.text_input("SurrealDB URL", value=settings.surrealdb_url)
        surrealdb_namespace = st.text_input("Namespace", value=settings.surrealdb_namespace)
        surrealdb_database = st.text_input("Database", value=settings.surrealdb_database)
        surrealdb_username = st.text_input("Username", value=settings.surrealdb_username)
        surrealdb_password = st.text_input("Password", value=settings.surrealdb_password, type="password")
        if st.form_submit_button("💾 Save Database Settings"):
            try:
                settings.surrealdb_url = surrealdb_url.strip()
                settings.surrealdb_namespace = surrealdb_namespace.strip()
                settings.surrealdb_database = surrealdb_database.strip()
                settings.surrealdb_username = surrealdb_username.strip()
                settings.surrealdb_password = surrealdb_password.strip()
                settings.save()
                st.success("✅ Database settings saved!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error saving database settings: {str(e)}")
                st.error(f"Failed to save database settings: {str(e)}")
    
    st.divider()
    
    st.subheader("Esperanto API Configuration")
    with st.form("esperanto_settings"):
        esperanto_base_url = st.text_input("Esperanto Base URL", value=settings.esperanto_base_url or "")
        esperanto_api_key = st.text_input("Esperanto API Key", value=settings.esperanto_api_key or "", type="password")
        if st.form_submit_button("💾 Save Esperanto Settings"):
            try:
                settings.esperanto_base_url = esperanto_base_url.strip() if esperanto_base_url.strip() else None
                settings.esperanto_api_key = esperanto_api_key.strip() if esperanto_api_key.strip() else None
                settings.save()
                st.success("✅ Esperanto settings saved!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error saving Esperanto settings: {str(e)}")
                st.error(f"Failed to save Esperanto settings: {str(e)}")
    
    st.divider()
    
    st.subheader("Other Settings")
    st.markdown("No additional settings available yet.")


if __name__ == "__main__":
    show_settings_page()
