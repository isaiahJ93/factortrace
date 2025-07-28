# In alembic/env.py, update the configuration section
from app.core.config import settings
from app.db.base import Base

# Update the run_migrations_online function
def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Use the DATABASE_URL from settings
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata
        )

        with context.begin_transaction():
            context.run_migrations()