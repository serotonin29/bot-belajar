import streamlit as st
from loguru import logger

from open_notebook.domain.models import Notebook, ChatSession, Note
from open_notebook.ai.models import model_manager
from open_notebook.exceptions import InvalidInputError, ConfigurationError


def show_chat_page():
    """Display the chat page for interacting with notebooks using AI."""
    st.title("💬 Chat with Your Notebook")
    
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
    
    # Chat session selection or creation
    chat_sessions = [cs for cs in ChatSession.get_all() if cs.notebook == notebook.id]
    chat_options = {cs.id: cs.name for cs in chat_sessions}
    
    if "selected_chat_session" not in st.session_state and chat_sessions:
        st.session_state.selected_chat_session = chat_sessions[0].id
    
    selected_chat_id = st.selectbox(
        "💬 Select Chat Session",
        options=[None] + list(chat_options.keys()),
        format_func=lambda x: chat_options[x] if x else "New chat session",
        index=0
    )
    st.session_state.selected_chat_session = selected_chat_id
    
    # Create new chat session
    if selected_chat_id is None:
        with st.form("create_chat_session"):
            chat_name = st.text_input("Chat Session Name", placeholder="Enter a name for this chat session")
            model_name = st.selectbox(
                "AI Model",
                options=[m for models in model_manager.get_available_models().values() for m in models],
                help="Choose the AI model for this chat session"
            )
            submitted = st.form_submit_button("💬 Start Chat")
            if submitted:
                if not chat_name.strip():
                    st.error("Chat session name is required")
                else:
                    try:
                        chat_session = ChatSession(
                            name=chat_name.strip(),
                            notebook=notebook.id,
                            model_name=model_name,
                            messages=[]
                        )
                        chat_session.save()
                        st.session_state.selected_chat_session = chat_session.id
                        st.success(f"✅ Chat session '{chat_name}' created!")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error creating chat session: {str(e)}")
                        st.error(f"Failed to create chat session: {str(e)}")
        return
    
    # Load selected chat session
    chat_session = ChatSession.get(selected_chat_id)
    st.subheader(f"💬 Chat: {chat_session.name}")
    st.caption(f"Model: {chat_session.model_name}")
    
    # Display chat history
    for msg in chat_session.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**AI:** {msg['content']}")
        elif msg["role"] == "system":
            st.markdown(f"**System:** {msg['content']}")
    
    st.divider()
    
    # Chat input
    with st.form("chat_input"):
        user_message = st.text_area("Your message", placeholder="Type your question or prompt here...", height=100)
        submitted = st.form_submit_button("💬 Send")
        if submitted:
            if not user_message.strip():
                st.error("Message cannot be empty")
            else:
                try:
                    # Add user message
                    chat_session.add_message("user", user_message.strip())
                    chat_session.save()
                    
                    # Get context notes
                    context_notes = chat_session.get_context_notes(user_message.strip(), limit=5)
                    context_text = "\n".join([note.content for note in context_notes])
                    
                    # Prepare messages for AI
                    messages = chat_session.messages.copy()
                    if context_text:
                        messages.insert(0, {"role": "system", "content": f"Relevant notes: {context_text}"})
                    
                    # Get AI response
                    with st.spinner("Thinking..."):
                        response = model_manager.chat_completion(
                            messages=messages,
                            model_name=chat_session.model_name
                        )
                    
                    # Add AI message
                    chat_session.add_message("assistant", response)
                    chat_session.save()
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error in chat: {str(e)}")
                    st.error(f"Failed to get AI response: {str(e)}")
    
    st.divider()
    
    # Option to delete chat session
    if st.button("🗑️ Delete Chat Session"):
        try:
            chat_session.delete()
            st.success("✅ Chat session deleted!")
            del st.session_state.selected_chat_session
            st.rerun()
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}")
            st.error(f"Failed to delete chat session: {str(e)}")


if __name__ == "__main__":
    show_chat_page()
