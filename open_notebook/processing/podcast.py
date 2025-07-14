from typing import List, Dict, Optional
import tempfile
import os
from pathlib import Path

from loguru import logger

from open_notebook.domain.models import Source, Note, Notebook
from open_notebook.exceptions import ProcessingError


class PodcastGenerator:
    """Handles podcast generation from content."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "opennotebook_podcasts"
        self.temp_dir.mkdir(exist_ok=True)
    
    def generate_from_sources(self, sources: List[Source], output_path: Optional[str] = None) -> str:
        """Generate a podcast from multiple sources."""
        try:
            from podcastfy.client import generate_podcast
            
            # Prepare content
            content_list = []
            for source in sources:
                if source.full_text:
                    content_list.append({
                        'title': source.title,
                        'content': source.full_text,
                        'url': source.url
                    })
            
            if not content_list:
                raise ProcessingError("No content available for podcast generation")
            
            # Generate output path if not provided
            if not output_path:
                output_path = str(self.temp_dir / f"podcast_{len(content_list)}_sources.mp3")
            
            # Generate podcast
            result = generate_podcast(
                content=content_list,
                output_file=output_path,
                config={
                    'conversation_style': 'educational',
                    'word_count': min(2000, sum(len(c['content'].split()) for c in content_list)),
                    'podcast_name': 'Open Notebook Podcast',
                    'podcast_tagline': 'AI-generated insights from your research'
                }
            )
            
            logger.info(f"Podcast generated: {output_path}")
            return output_path
            
        except ImportError:
            raise ProcessingError("Podcastfy library not available. Install with: pip install podcastfy")
        except Exception as e:
            logger.error(f"Error generating podcast: {str(e)}")
            raise ProcessingError(f"Failed to generate podcast: {str(e)}")
    
    def generate_from_notes(self, notes: List[Note], output_path: Optional[str] = None) -> str:
        """Generate a podcast from notes."""
        try:
            from podcastfy.client import generate_podcast
            
            # Prepare content from notes
            content_list = []
            for note in notes:
                content_list.append({
                    'title': f"Note: {note.id}",
                    'content': note.content,
                    'metadata': note.metadata
                })
            
            if not content_list:
                raise ProcessingError("No notes available for podcast generation")
            
            # Generate output path if not provided
            if not output_path:
                output_path = str(self.temp_dir / f"podcast_{len(content_list)}_notes.mp3")
            
            # Generate podcast
            result = generate_podcast(
                content=content_list,
                output_file=output_path,
                config={
                    'conversation_style': 'conversational',
                    'word_count': min(1500, sum(len(c['content'].split()) for c in content_list)),
                    'podcast_name': 'Open Notebook Notes',
                    'podcast_tagline': 'Your notes in podcast form'
                }
            )
            
            logger.info(f"Podcast generated from notes: {output_path}")
            return output_path
            
        except ImportError:
            raise ProcessingError("Podcastfy library not available. Install with: pip install podcastfy")
        except Exception as e:
            logger.error(f"Error generating podcast from notes: {str(e)}")
            raise ProcessingError(f"Failed to generate podcast: {str(e)}")
    
    def generate_from_notebook(self, notebook: Notebook, include_sources: bool = True, include_notes: bool = True, output_path: Optional[str] = None) -> str:
        """Generate a podcast from an entire notebook."""
        try:
            content_list = []
            
            # Add sources if requested
            if include_sources:
                sources = notebook.get_sources()
                for source in sources:
                    if source.full_text:
                        content_list.append({
                            'title': f"Source: {source.title}",
                            'content': source.full_text,
                            'url': source.url,
                            'type': 'source'
                        })
            
            # Add notes if requested
            if include_notes:
                notes = notebook.get_notes()
                for note in notes:
                    content_list.append({
                        'title': f"Note: {note.id}",
                        'content': note.content,
                        'type': 'note'
                    })
            
            if not content_list:
                raise ProcessingError("No content available in notebook for podcast generation")
            
            # Generate output path if not provided
            if not output_path:
                safe_name = "".join(c for c in notebook.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = str(self.temp_dir / f"podcast_{safe_name}.mp3")
            
            # Generate podcast
            from podcastfy.client import generate_podcast
            
            result = generate_podcast(
                content=content_list,
                output_file=output_path,
                config={
                    'conversation_style': 'educational',
                    'word_count': min(3000, sum(len(str(c['content']).split()) for c in content_list)),
                    'podcast_name': f'Open Notebook: {notebook.name}',
                    'podcast_tagline': notebook.description or 'AI-generated insights from your research'
                }
            )
            
            logger.info(f"Podcast generated for notebook '{notebook.name}': {output_path}")
            return output_path
            
        except ImportError:
            raise ProcessingError("Podcastfy library not available. Install with: pip install podcastfy")
        except Exception as e:
            logger.error(f"Error generating podcast for notebook: {str(e)}")
            raise ProcessingError(f"Failed to generate podcast: {str(e)}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary podcast files."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in self.temp_dir.glob("*.mp3"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        logger.info(f"Cleaned up old podcast file: {file_path}")
                        
        except Exception as e:
            logger.warning(f"Error during podcast cleanup: {str(e)}")


def get_podcast_generator() -> PodcastGenerator:
    """Get the podcast generator instance."""
    return PodcastGenerator()
