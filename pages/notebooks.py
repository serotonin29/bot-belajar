import streamlit as st
from loguru import logger

from open_notebook.domain.models import Notebook
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


def show_notebooks_page():
    """Display the notebooks management page."""
    st.title("📚 Notebooks")
    
    # Create new notebook section
    with st.expander("➕ Create New Notebook", expanded=False):
        with st.form("create_notebook"):
            name = st.text_input("Notebook Name", placeholder="Enter notebook name...")
            description = st.text_area("Description (optional)", placeholder="Describe your notebook...")
            
            submitted = st.form_submit_button("Create Notebook")
            
            if submitted:
                if not name.strip():
                    st.error("Notebook name is required")
                else:
                    try:
                        notebook = Notebook(
                            name=name.strip(),
                            description=description.strip() if description else None
                        )
                        notebook.save()
                        st.success(f"✅ Notebook '{name}' created successfully!")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error creating notebook: {str(e)}")
                        st.error(f"Failed to create notebook: {str(e)}")
    
    # List existing notebooks
    try:
        notebooks = Notebook.get_all(order_by="created DESC")
        
        if not notebooks:
            st.info("📝 No notebooks yet. Create your first notebook above!")
            return
        
        st.subheader(f"Your Notebooks ({len(notebooks)})")
        
        # Display notebooks in a grid-like layout
        cols = st.columns(2)
        for i, notebook in enumerate(notebooks):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"### 📓 {notebook.name}")
                    
                    if notebook.description:
                        st.markdown(f"*{notebook.description}*")
                    
                    # Get counts
                    try:
                        sources = notebook.get_sources()
                        notes = notebook.get_notes()
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Sources", len(sources))
                        with col2:
                            st.metric("Notes", len(notes))
                        with col3:
                            if notebook.created:
                                st.caption(f"Created: {notebook.created.strftime('%Y-%m-%d')}")
                    
                    except Exception as e:
                        logger.warning(f"Error getting notebook stats: {str(e)}")
                        st.caption("Unable to load stats")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📖 Open", key=f"open_{notebook.id}"):
                            st.session_state.selected_notebook = notebook.id
                            st.switch_page("pages/sources.py")
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{notebook.id}"):
                            st.session_state.edit_notebook_id = notebook.id
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{notebook.id}"):
                            st.session_state.delete_notebook_id = notebook.id
                    
                    st.divider()
        
        # Handle edit notebook
        if "edit_notebook_id" in st.session_state:
            notebook_id = st.session_state.edit_notebook_id
            notebook = Notebook.get(notebook_id)
            
            st.subheader("✏️ Edit Notebook")
            
            with st.form("edit_notebook"):
                new_name = st.text_input("Notebook Name", value=notebook.name)
                new_description = st.text_area("Description", value=notebook.description or "")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        try:
                            notebook.name = new_name.strip()
                            notebook.description = new_description.strip() if new_description else None
                            notebook.save()
                            st.success("✅ Notebook updated successfully!")
                            del st.session_state.edit_notebook_id
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error updating notebook: {str(e)}")
                            st.error(f"Failed to update notebook: {str(e)}")
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.edit_notebook_id
                        st.rerun()
        
        # Handle delete notebook
        if "delete_notebook_id" in st.session_state:
            notebook_id = st.session_state.delete_notebook_id
            notebook = Notebook.get(notebook_id)
            
            st.error(f"⚠️ Are you sure you want to delete notebook '{notebook.name}'?")
            st.warning("This action cannot be undone. All sources and notes in this notebook will also be deleted.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Delete", type="primary"):
                    try:
                        # Delete related sources and notes first
                        sources = notebook.get_sources()
                        notes = notebook.get_notes()
                        
                        for source in sources:
                            source.delete()
                        
                        for note in notes:
                            note.delete()
                        
                        # Delete the notebook
                        notebook.delete()
                        
                        st.success(f"✅ Notebook '{notebook.name}' deleted successfully!")
                        del st.session_state.delete_notebook_id
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Error deleting notebook: {str(e)}")
                        st.error(f"Failed to delete notebook: {str(e)}")
            
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.delete_notebook_id
                    st.rerun()
    
    except Exception as e:
        logger.error(f"Error loading notebooks: {str(e)}")
        st.error(f"Failed to load notebooks: {str(e)}")


if __name__ == "__main__":
    show_notebooks_page()
