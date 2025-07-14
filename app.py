import streamlit as st
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# Page configuration
st.set_page_config(
    page_title="Open Notebook",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
    .stButton > button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-success {
        background-color: #28a745;
    }
    .status-warning {
        background-color: #ffc107;
    }
    .status-error {
        background-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📚 Open Notebook")
        st.markdown("*AI-powered research companion*")
        
        # Navigation menu
        page = st.selectbox(
            "Navigate to:",
            [
                "🏠 Home",
                "📚 Notebooks", 
                "📄 Sources",
                "📝 Notes",
                "💬 Chat",
                "🤖 Models",
                "⚙️ Settings",
                "🎧 Podcast"
            ],
            format_func=lambda x: x
        )
        
        st.divider()
        
        # Quick stats (if available)
        try:
            from open_notebook.domain.models import Notebook, Source, Note
            
            notebooks = Notebook.get_all()
            total_sources = 0
            total_notes = 0
            
            for notebook in notebooks:
                try:
                    sources = notebook.get_sources()
                    notes = notebook.get_notes()
                    total_sources += len(sources)
                    total_notes += len(notes)
                except:
                    pass
            
            st.markdown("### 📊 Quick Stats")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Notebooks", len(notebooks))
            with col2:
                st.metric("Sources", total_sources)
            with col3:
                st.metric("Notes", total_notes)
                
        except Exception as e:
            st.markdown("### 📊 Quick Stats")
            st.caption("Stats unavailable - setup required")
        
        st.divider()
        
        # System status
        st.markdown("### 🔧 System Status")
        
        # Database status
        try:
            from open_notebook.database.repository import test_connection
            if test_connection():
                st.markdown('<span class="status-indicator status-success"></span>Database Connected', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-indicator status-error"></span>Database Disconnected', unsafe_allow_html=True)
        except:
            st.markdown('<span class="status-indicator status-error"></span>Database Error', unsafe_allow_html=True)
        
        # AI Models status
        try:
            from open_notebook.ai.models import model_manager
            configured_providers = model_manager.get_configured_providers()
            if configured_providers:
                st.markdown(f'<span class="status-indicator status-success"></span>AI Models ({len(configured_providers)} providers)', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-indicator status-warning"></span>AI Models (No API keys)', unsafe_allow_html=True)
        except:
            st.markdown('<span class="status-indicator status-error"></span>AI Models Error', unsafe_allow_html=True)
    
    # Main content area
    if page == "🏠 Home":
        show_home_page()
    elif page == "📚 Notebooks":
        st.switch_page("pages/notebooks.py")
    elif page == "📄 Sources":
        st.switch_page("pages/sources.py")
    elif page == "📝 Notes":
        st.switch_page("pages/notes.py")
    elif page == "💬 Chat":
        st.switch_page("pages/chat.py")
    elif page == "🤖 Models":
        st.switch_page("pages/models.py")
    elif page == "⚙️ Settings":
        st.switch_page("pages/settings.py")
    elif page == "🎧 Podcast":
        st.switch_page("pages/podcast.py")


def show_home_page():
    """Display the home page."""
    st.title("📚 Welcome to Open Notebook")
    st.markdown("### *Your AI-powered research companion*")
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Open Notebook helps you organize, analyze, and interact with your research materials using AI. 
        Create notebooks, add sources, take notes, and chat with your content using state-of-the-art language models.
        
        **Key Features:**
        - 📚 **Organize** your research into notebooks
        - 📄 **Import** content from URLs, files, and text
        - 📝 **Take notes** and link them to sources  
        - 💬 **Chat** with your content using AI
        - 🎧 **Generate podcasts** from your research
        - 🤖 **Multiple AI providers** (OpenAI, Anthropic, Gemini, etc.)
        """)
    
    with col2:
        st.image("https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=Open+Notebook", caption="AI Research Assistant")
    
    st.divider()
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 Create Notebook", use_container_width=True):
            st.switch_page("pages/notebooks.py")
    
    with col2:
        if st.button("📄 Add Source", use_container_width=True):
            st.switch_page("pages/sources.py")
    
    with col3:
        if st.button("🤖 Setup AI", use_container_width=True):
            st.switch_page("pages/models.py")
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/settings.py")
    
    st.divider()
    
    # Recent activity / Getting started
    try:
        from open_notebook.domain.models import Notebook
        notebooks = Notebook.get_all(order_by="created DESC")
        
        if notebooks:
            st.markdown("### 📋 Recent Notebooks")
            
            for notebook in notebooks[:3]:  # Show last 3 notebooks
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**📓 {notebook.name}**")
                        if notebook.description:
                            st.caption(notebook.description)
                    
                    with col2:
                        try:
                            sources = notebook.get_sources()
                            notes = notebook.get_notes()
                            st.caption(f"{len(sources)} sources, {len(notes)} notes")
                        except:
                            st.caption("Stats unavailable")
                    
                    with col3:
                        if st.button("Open", key=f"open_{notebook.id}"):
                            st.session_state.selected_notebook = notebook.id
                            st.switch_page("pages/sources.py")
                    
                    st.divider()
        else:
            show_getting_started()
    
    except Exception as e:
        logger.warning(f"Could not load notebooks: {str(e)}")
        show_getting_started()


def show_getting_started():
    """Show getting started guide for new users."""
    st.markdown("### 🌟 Getting Started")
    
    st.markdown("""
    Welcome to Open Notebook! Here's how to get started:
    
    1. **📚 Create your first notebook** - Organize your research by topic
    2. **🔑 Configure AI models** - Add API keys for AI-powered features  
    3. **📄 Add sources** - Import content from URLs, files, or text
    4. **📝 Take notes** - Capture insights and link them to sources
    5. **💬 Start chatting** - Ask questions about your content using AI
    """)
    
    # Setup checklist
    st.markdown("### ✅ Setup Checklist")
    
    checklist_items = []
    
    # Check database
    try:
        from open_notebook.database.repository import test_connection
        db_status = test_connection()
        checklist_items.append(("Database connection", db_status))
    except:
        checklist_items.append(("Database connection", False))
    
    # Check AI models
    try:
        from open_notebook.ai.models import model_manager
        ai_status = len(model_manager.get_configured_providers()) > 0
        checklist_items.append(("AI model configuration", ai_status))
    except:
        checklist_items.append(("AI model configuration", False))
    
    # Check notebooks
    try:
        from open_notebook.domain.models import Notebook
        notebooks = Notebook.get_all()
        notebook_status = len(notebooks) > 0
        checklist_items.append(("First notebook created", notebook_status))
    except:
        checklist_items.append(("First notebook created", False))
    
    for item, status in checklist_items:
        icon = "✅" if status else "❌"
        st.markdown(f"{icon} {item}")
    
    # Next steps
    incomplete_items = [item for item, status in checklist_items if not status]
    if incomplete_items:
        st.markdown("### 👉 Next Steps")
        if not checklist_items[0][1]:  # Database
            st.info("🔧 Start the database with: `docker-compose up -d`")
        elif not checklist_items[1][1]:  # AI
            st.info("🤖 Configure AI models in the Models page")
        elif not checklist_items[2][1]:  # Notebooks
            st.info("📚 Create your first notebook to get started")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.exception("Application error")
        
        # Show basic setup instructions on error
        st.markdown("""
        ### 🔧 Setup Required
        
        It looks like Open Notebook needs to be set up. Please ensure:
        
        1. **Dependencies installed**: `pip install -r requirements.txt`
        2. **Database running**: `docker-compose up -d`
        3. **Environment configured**: Copy `.env.example` to `.env` and configure
        
        Then restart the application.
        """)
