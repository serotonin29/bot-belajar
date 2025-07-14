import streamlit as st
from loguru import logger

from open_notebook.domain.models import Notebook, Source
from open_notebook.processing.content import get_content_processor, get_esperanto_processor
from open_notebook.exceptions import ProcessingError, InvalidInputError


def show_sources_page():
    """Display the sources management page."""
    st.title("📄 Sources")
    
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
    
    # Add new source section
    st.subheader("➕ Add New Source")
    
    source_type = st.radio(
        "Source Type",
        ["URL", "File Upload", "Text Input"],
        horizontal=True
    )
    
    if source_type == "URL":
        with st.form("add_url_source"):
            url = st.text_input("URL", placeholder="https://example.com/article")
            title = st.text_input("Title (optional)", placeholder="Custom title for this source")
            
            use_esperanto = st.checkbox("Use Esperanto API for enhanced processing", value=False)
            
            submitted = st.form_submit_button("📥 Add URL Source")
            
            if submitted:
                if not url.strip():
                    st.error("URL is required")
                else:
                    try:
                        with st.spinner("Processing URL..."):
                            processor = get_content_processor()
                            
                            if use_esperanto:
                                esperanto = get_esperanto_processor()
                                if esperanto.is_available():
                                    try:
                                        result = esperanto.process_url(url)
                                        # Create source from Esperanto result
                                        source = Source(
                                            title=title or result.get('title', url),
                                            url=url,
                                            content=result.get('summary', '')[:10000],
                                            full_text=result.get('content', ''),
                                            metadata=result.get('metadata', {}),
                                            is_processed=True
                                        )
                                        source.save()
                                        notebook.add_source(source)
                                    except Exception as e:
                                        st.warning(f"Esperanto processing failed, falling back to basic processing: {str(e)}")
                                        source = processor.process_url(url, notebook.id, title)
                                else:
                                    st.warning("Esperanto API not configured, using basic processing")
                                    source = processor.process_url(url, notebook.id, title)
                            else:
                                source = processor.process_url(url, notebook.id, title)
                            
                        st.success(f"✅ URL source '{source.title}' added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error adding URL source: {str(e)}")
                        st.error(f"Failed to add URL source: {str(e)}")
    
    elif source_type == "File Upload":
        with st.form("add_file_source"):
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'md', 'py', 'js', 'html', 'css', 'pdf', 'doc', 'docx'],
                help="Supported formats: Text files, Markdown, Code files, PDFs, Word documents"
            )
            title = st.text_input("Title (optional)", placeholder="Custom title for this source")
            
            submitted = st.form_submit_button("📤 Upload File")
            
            if submitted:
                if uploaded_file is None:
                    st.error("Please select a file")
                else:
                    try:
                        with st.spinner("Processing file..."):
                            processor = get_content_processor()
                            source = processor.process_file(uploaded_file, notebook.id, title)
                        
                        st.success(f"✅ File source '{source.title}' added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error adding file source: {str(e)}")
                        st.error(f"Failed to add file source: {str(e)}")
    
    else:  # Text Input
        with st.form("add_text_source"):
            title = st.text_input("Title", placeholder="Enter a title for this text source")
            text_content = st.text_area(
                "Content",
                placeholder="Paste or type your content here...",
                height=200
            )
            
            submitted = st.form_submit_button("📝 Add Text Source")
            
            if submitted:
                if not title.strip():
                    st.error("Title is required")
                elif not text_content.strip():
                    st.error("Content is required")
                else:
                    try:
                        processor = get_content_processor()
                        source = processor.process_text(text_content, notebook.id, title)
                        
                        st.success(f"✅ Text source '{source.title}' added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error adding text source: {str(e)}")
                        st.error(f"Failed to add text source: {str(e)}")
    
    st.divider()
    
    # List existing sources
    try:
        sources = notebook.get_sources()
        
        if not sources:
            st.info("📄 No sources in this notebook yet. Add your first source above!")
            return
        
        st.subheader(f"Sources in {notebook.name} ({len(sources)})")
        
        # Display sources
        for source in sources:
            with st.expander(f"📄 {source.title}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if source.url:
                        st.markdown(f"**URL:** {source.url}")
                    
                    if source.description:
                        st.markdown(f"**Description:** {source.description}")
                    
                    if source.content:
                        st.markdown("**Content Preview:**")
                        st.text(source.content[:500] + "..." if len(source.content) > 500 else source.content)
                    
                    # Metadata
                    if source.metadata:
                        with st.expander("📊 Metadata"):
                            st.json(source.metadata)
                    
                    # Status indicators
                    col_status1, col_status2, col_status3 = st.columns(3)
                    with col_status1:
                        status = "✅ Processed" if source.is_processed else "⏳ Pending"
                        st.caption(f"Status: {status}")
                    
                    with col_status2:
                        has_doc = "📎 Has Document" if source.has_document else "📄 Text Only"
                        st.caption(has_doc)
                    
                    with col_status3:
                        if source.created:
                            st.caption(f"Added: {source.created.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    # Action buttons
                    if st.button("📝 Notes", key=f"notes_{source.id}"):
                        st.session_state.selected_source = source.id
                        st.switch_page("pages/notes.py")
                    
                    if st.button("✏️ Edit", key=f"edit_source_{source.id}"):
                        st.session_state.edit_source_id = source.id
                    
                    if st.button("🗑️ Delete", key=f"delete_source_{source.id}"):
                        st.session_state.delete_source_id = source.id
        
        # Handle edit source
        if "edit_source_id" in st.session_state:
            source_id = st.session_state.edit_source_id
            source = Source.get(source_id)
            
            st.subheader("✏️ Edit Source")
            
            with st.form("edit_source"):
                new_title = st.text_input("Title", value=source.title)
                new_description = st.text_area("Description", value=source.description or "")
                new_url = st.text_input("URL", value=source.url or "")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        try:
                            source.title = new_title.strip()
                            source.description = new_description.strip() if new_description else None
                            source.url = new_url.strip() if new_url else None
                            source.save()
                            st.success("✅ Source updated successfully!")
                            del st.session_state.edit_source_id
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error updating source: {str(e)}")
                            st.error(f"Failed to update source: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.edit_source_id
                        st.rerun()
        
        # Handle delete source
        if "delete_source_id" in st.session_state:
            source_id = st.session_state.delete_source_id
            source = Source.get(source_id)
            
            st.error(f"⚠️ Are you sure you want to delete source '{source.title}'?")
            st.warning("This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Delete", type="primary"):
                    try:
                        # Remove from notebook and delete
                        notebook.remove_source(source)
                        source.delete()
                        
                        st.success(f"✅ Source '{source.title}' deleted successfully!")
                        del st.session_state.delete_source_id
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error deleting source: {str(e)}")
                        st.error(f"Failed to delete source: {str(e)}")
            
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.delete_source_id
                    st.rerun()
    
    except Exception as e:
        logger.error(f"Error loading sources: {str(e)}")
        st.error(f"Failed to load sources: {str(e)}")


if __name__ == "__main__":
    show_sources_page()
