import streamlit as st
from loguru import logger

from open_notebook.domain.models import Settings
from open_notebook.ai.models import model_manager
from open_notebook.exceptions import ConfigurationError


def show_models_page():
    """Display the AI models management page."""
    st.title("🤖 Model AI (Gemini)")
    settings = Settings.load()

    st.subheader("🔑 Konfigurasi API Key Gemini")
    with st.form("api_gemini"):
        gemini_key = st.text_input(
            "Gemini API Key",
            value=settings.gemini_api_key or "",
            type="password",
            help="Masukkan API key Gemini Anda dari Google AI Studio"
        )
        if st.form_submit_button("💾 Simpan API Key"):
            try:
                settings.gemini_api_key = gemini_key.strip() if gemini_key.strip() else None
                settings.save()
                model_manager.refresh_settings()
                st.success("✅ API key berhasil disimpan!")
                st.rerun()
            except Exception as e:
                logger.error(f"Gagal menyimpan API key: {str(e)}")
                st.error(f"Gagal menyimpan API key: {str(e)}")

    st.divider()
    st.subheader("⚙️ Pengaturan Model Gemini")
    with st.form("pengaturan_model"):
        default_model = st.selectbox(
            "Model Default",
            options=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            index=["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"].index(settings.default_model) if settings.default_model in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"] else 0,
            help="Pilih model Gemini yang akan digunakan"
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=settings.default_temperature,
            step=0.1,
            help="Kontrol kreativitas jawaban AI"
        )
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=32000,
            value=settings.max_tokens,
            step=100,
            help="Jumlah token maksimal dalam respon"
        )
        if st.form_submit_button("💾 Simpan Pengaturan Model"):
            try:
                settings.default_model = default_model
                settings.default_temperature = temperature
                settings.max_tokens = max_tokens
                settings.save()
                st.success("✅ Pengaturan model berhasil disimpan!")
                st.rerun()
            except Exception as e:
                logger.error(f"Gagal menyimpan pengaturan model: {str(e)}")
                st.error(f"Gagal menyimpan pengaturan model: {str(e)}")

    st.divider()
    st.subheader("🧪 Tes Model Gemini")
    with st.form("tes_model_gemini"):
        test_prompt = st.text_area(
            "Prompt Tes",
            value="Jelaskan AI Gemini dalam bahasa sederhana.",
            help="Masukkan prompt untuk menguji model Gemini"
        )
        test_temperature = st.slider(
            "Temperature Tes",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
        if st.form_submit_button("🚀 Jalankan Tes"):
            if test_prompt.strip():
                with st.spinner(f"Mengetes model {settings.default_model}..."):
                    try:
                        response = model_manager.chat_completion(
                            messages=[{"role": "user", "content": test_prompt}],
                            model_name=settings.default_model,
                            temperature=test_temperature
                        )
                        st.success("✅ Tes berhasil!")
                        st.markdown("**Respon:**")
                        st.markdown(response)
                    except Exception as e:
                        logger.error(f"Tes model gagal: {str(e)}")
                        st.error(f"Tes gagal: {str(e)}")
            else:
                st.error("Prompt tes wajib diisi")


if __name__ == "__main__":
    show_models_page()
