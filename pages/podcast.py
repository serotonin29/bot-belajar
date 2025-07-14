import streamlit as st
from loguru import logger

from open_notebook.domain.models import Notebook
from open_notebook.processing.podcast import get_podcast_generator
from open_notebook.exceptions import ProcessingError


def show_podcast_page():
    """Display the podcast generation page."""
    st.title("🎧 Podcast Generator")
    
    # Notebook selection
    notebooks = Notebook.get_all(order_by="created DESC")
    if not notebooks:
        st.warning("📝 No notebooks found. Please create a notebook first.")
        if st.button("➕ Create Notebook"):
            st.switch_page("pages/notebooks.py")
        return
    
    # Get selected notebook
    if "selected_notebook" not in st.session_state:
        st.session_state.selected_notebook = notebooks[0].id
    
    notebook_options = {nb.id: nb.name for nb in notebooks}
    selected_notebook_id = st.selectbox(
        "📚 Select Notebook",
        options=list(notebook_options.keys()),
        format_func=lambda x: notebook_options[x],
        index=list(notebook_options.keys()).index(st.session_state.selected_notebook) if st.session_state.selected_notebook in notebook_options else 0
    )
    st.session_state.selected_notebook = selected_notebook_id
    notebook = Notebook.get(selected_notebook_id)
    
    st.subheader("Podcast Options")
    include_sources = st.checkbox("Include sources", value=True)
    include_notes = st.checkbox("Include notes", value=True)
    
    st.markdown("Generate a podcast from your notebook's content. The podcast will be saved as an MP3 file.")
    
    if st.button("🎧 Generate Podcast"):
        with st.spinner("Generating podcast..."):
            try:
                generator = get_podcast_generator()
                output_path = generator.generate_from_notebook(
                    notebook,
                    include_sources=include_sources,
                    include_notes=include_notes
                )
                st.success(f"✅ Podcast generated: {output_path}")
                st.audio(output_path)
            except Exception as e:
                logger.error(f"Error generating podcast: {str(e)}")
                st.error(f"Failed to generate podcast: {str(e)}")
    
    st.divider()
    
    st.subheader("Podcast Cleanup")
    if st.button("🧹 Clean Up Old Podcasts"):
        try:
            generator = get_podcast_generator()
            generator.cleanup_temp_files(max_age_hours=24)
            st.success("✅ Old podcast files cleaned up!")
        except Exception as e:
            logger.warning(f"Error cleaning up podcasts: {str(e)}")
            st.error(f"Failed to clean up podcasts: {str(e)}")


if __name__ == "__main__":
    show_podcast_page()
