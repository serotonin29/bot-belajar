import streamlit as st
from loguru import logger

from open_notebook.domain.models import Notebook, Source, Note
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


def show_notes_page():
    """Display the notes management page."""
    st.title("📝 Notes")
    
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
    
    # Source selection
    sources = notebook.get_sources()
    source_options = {src.id: src.title for src in sources}
    selected_source_id = st.selectbox(
        "📄 Select Source (optional)",
        options=[None] + list(source_options.keys()),
        format_func=lambda x: source_options[x] if x else "All sources",
        index=0
    )
    
    # Add new note section
    st.subheader("➕ Add New Note")
    with st.form("add_note"):
        note_content = st.text_area("Note Content", placeholder="Type your note here...", height=150)
        submitted = st.form_submit_button("📝 Add Note")
        if submitted:
            if not note_content.strip():
                st.error("Note content is required")
            else:
                try:
                    note = Note(
                        content=note_content.strip(),
                        notebook=notebook.id,
                        source=selected_source_id if selected_source_id else None
                    )
                    note.save()
                    st.success("✅ Note added successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error adding note: {str(e)}")
                    st.error(f"Failed to add note: {str(e)}")
    
    st.divider()
    
    # List existing notes
    try:
        if selected_source_id:
            notes = [note for note in notebook.get_notes() if note.source == selected_source_id]
        else:
            notes = notebook.get_notes()
        
        if not notes:
            st.info("📝 No notes yet. Add your first note above!")
            return
        
        st.subheader(f"Notes in {notebook.name} ({len(notes)})")
        
        for note in notes:
            with st.expander(f"📝 Note {note.id}", expanded=False):
                st.markdown(f"**Content:**\n{note.content}")
                if note.source:
                    source = Source.get(note.source)
                    st.caption(f"Source: {source.title}")
                if note.created:
                    st.caption(f"Created: {note.created.strftime('%Y-%m-%d %H:%M')}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_note_{note.id}"):
                        st.session_state.edit_note_id = note.id
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_note_{note.id}"):
                        st.session_state.delete_note_id = note.id
        
        # Handle edit note
        if "edit_note_id" in st.session_state:
            note_id = st.session_state.edit_note_id
            note = Note.get(note_id)
            st.subheader("✏️ Edit Note")
            with st.form("edit_note"):
                new_content = st.text_area("Note Content", value=note.content, height=150)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        try:
                            note.content = new_content.strip()
                            note.save()
                            st.success("✅ Note updated successfully!")
                            del st.session_state.edit_note_id
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error updating note: {str(e)}")
                            st.error(f"Failed to update note: {str(e)}")
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.edit_note_id
                        st.rerun()
        
        # Handle delete note
        if "delete_note_id" in st.session_state:
            note_id = st.session_state.delete_note_id
            note = Note.get(note_id)
            st.error(f"⚠️ Are you sure you want to delete this note?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Delete", type="primary"):
                    try:
                        note.delete()
                        st.success("✅ Note deleted successfully!")
                        del st.session_state.delete_note_id
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error deleting note: {str(e)}")
                        st.error(f"Failed to delete note: {str(e)}")
            with col2:
                if st.button("❌ Cancel"):
                    del st.session_state.delete_note_id
                    st.rerun()
    except Exception as e:
        logger.error(f"Error loading notes: {str(e)}")
        st.error(f"Failed to load notes: {str(e)}")


if __name__ == "__main__":
    show_notes_page()
