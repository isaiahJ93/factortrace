# app/db/seeds/__init__.py
"""
Database Seed Runner

Provides run_all_seeds() function and CLI entry point for seeding
reference data into the database.

Usage:
    python -m app.db.seeds

Or programmatically:
    from app.db.seeds import run_all_seeds
    run_all_seeds()
"""
import logging
import sys
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.db.seeds.cbam_seed import run_cbam_seed
from app.db.seeds.eudr_seed import run_eudr_seed
from app.db.seeds.emission_factors_seed import run_emission_factors_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_all_seeds(db: Optional[Session] = None) -> dict:
    """
    Run all database seeds.

    Args:
        db: Optional database session. If not provided, creates one.

    Returns:
        Summary dict with counts of inserted records per seed.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        logger.info("=" * 60)
        logger.info("Starting Database Seed Runner")
        logger.info("=" * 60)

        results = {}

        # 1. Seed CBAM reference data
        logger.info("\n[1/3] Seeding CBAM reference data...")
        cbam_results = run_cbam_seed(db)
        results["cbam"] = cbam_results

        # 2. Seed EUDR reference data
        logger.info("\n[2/3] Seeding EUDR reference data...")
        eudr_results = run_eudr_seed(db)
        results["eudr"] = eudr_results

        # 3. Seed core emission factors
        logger.info("\n[3/3] Seeding emission factors...")
        emission_factors_results = run_emission_factors_seed(db)
        results["emission_factors"] = emission_factors_results

        logger.info("\n" + "=" * 60)
        logger.info("Database Seed Runner Complete!")
        logger.info("=" * 60)
        logger.info(f"\nSummary:")
        logger.info(f"  CBAM Products:        {cbam_results.get('cbam_products', 0)}")
        logger.info(f"  CBAM Factor Sources:  {cbam_results.get('cbam_factor_sources', 0)}")
        logger.info(f"  CBAM Emission Factors: {cbam_results.get('cbam_emission_factors', 0)}")
        logger.info(f"  EUDR Commodities:     {eudr_results.get('eudr_commodities', 0)}")
        logger.info(f"  Emission Factors:     {emission_factors_results.get('emission_factors', 0)}")

        return results

    except Exception as e:
        logger.error(f"Seed runner failed: {e}")
        db.rollback()
        raise

    finally:
        if close_session:
            db.close()


def create_tables():
    """Create all database tables if they don't exist."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="FactorTrace Database Seed Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app.db.seeds              # Run all seeds
    python -m app.db.seeds --create     # Create tables first, then seed
    python -m app.db.seeds --cbam-only  # Seed only CBAM data
    python -m app.db.seeds --eudr-only  # Seed only EUDR data
    python -m app.db.seeds --factors-only  # Seed only emission factors
        """
    )

    parser.add_argument(
        "--create",
        action="store_true",
        help="Create database tables before seeding"
    )
    parser.add_argument(
        "--cbam-only",
        action="store_true",
        help="Seed only CBAM reference data"
    )
    parser.add_argument(
        "--eudr-only",
        action="store_true",
        help="Seed only EUDR reference data"
    )
    parser.add_argument(
        "--factors-only",
        action="store_true",
        help="Seed only emission factors"
    )

    args = parser.parse_args()

    try:
        # Optionally create tables first
        if args.create:
            create_tables()

        # Run selected seeds
        db = SessionLocal()
        try:
            if args.cbam_only:
                logger.info("Running CBAM seed only...")
                run_cbam_seed(db)
            elif args.eudr_only:
                logger.info("Running EUDR seed only...")
                run_eudr_seed(db)
            elif args.factors_only:
                logger.info("Running emission factors seed only...")
                run_emission_factors_seed(db)
            else:
                # Run all seeds
                run_all_seeds(db)

            logger.info("\nSeeding completed successfully!")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
