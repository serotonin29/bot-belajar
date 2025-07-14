import os

from loguru import logger
from sblpy.connection import SurrealSyncConnection
from sblpy.migrations.db_processes import get_latest_version
from sblpy.migrations.migrations import Migration
from sblpy.migrations.runner import MigrationRunner


class MigrationManager:
    def __init__(self):
        self.connection = SurrealSyncConnection(
            host=os.environ["SURREAL_ADDRESS"],
            port=int(os.environ["SURREAL_PORT"]),
            user=os.environ["SURREAL_USER"],
            password=os.environ["SURREAL_PASS"],
            namespace=os.environ["SURREAL_NAMESPACE"],
            database=os.environ["SURREAL_DATABASE"],
            encrypted=False,
        )
        self.runner = MigrationRunner(self.connection)

    def get_current_version(self) -> int:
        try:
            return get_latest_version(self.connection)
        except Exception:
            return 0

    @property
    def needs_migration(self) -> bool:
        current_version = self.get_current_version()
        latest_version = 1  # Update this as you add more migrations
        return current_version < latest_version

    def run_migration_up(self):
        logger.info("Running database migrations...")
        
        # Define your migrations here
        migrations = [
            Migration(
                name="001_initial_schema",
                version=1,
                up_queries=[
                    "DEFINE TABLE notebook;",
                    "DEFINE TABLE source;",
                    "DEFINE TABLE note;",
                    "DEFINE TABLE chat_session;",
                    "DEFINE TABLE source_insight;",
                    "DEFINE TABLE source_embedding;",
                    "DEFINE TABLE model;",
                    "DEFINE TABLE transformation;",
                    "DEFINE TABLE podcast_config;",
                    "DEFINE TABLE podcast_episode;",
                    "DEFINE TABLE reference;",
                ],
                down_queries=[
                    "REMOVE TABLE notebook;",
                    "REMOVE TABLE source;",
                    "REMOVE TABLE note;",
                    "REMOVE TABLE chat_session;",
                    "REMOVE TABLE source_insight;",
                    "REMOVE TABLE source_embedding;",
                    "REMOVE TABLE model;",
                    "REMOVE TABLE transformation;",
                    "REMOVE TABLE podcast_config;",
                    "REMOVE TABLE podcast_episode;",
                    "REMOVE TABLE reference;",
                ]
            )
        ]
        
        for migration in migrations:
            self.runner.run_up(migration)
            
        logger.info("Database migrations completed successfully")
