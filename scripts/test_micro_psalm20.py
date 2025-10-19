"""
Test script to re-run Micro agent for Psalm 20
This will show the detailed research requests and results
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.micro_analyst import MicroAnalystV2
from src.schemas.analysis_schemas import load_macro_analysis
from src.utils.logger import get_logger

# Set up logger
logger = get_logger("test_micro_psalm20")

# Paths
macro_file = Path("output/test_psalm_20_phase4/psalm_020_macro.json")
output_dir = Path("output/test_psalm_20_phase4")

# Load macro analysis
logger.info("Loading macro analysis...")
macro_analysis = load_macro_analysis(str(macro_file))

# Run micro analysis
logger.info("\nRunning MicroAnalyst v2 for Psalm 20...")
logger.info("=" * 80)

micro_analyst = MicroAnalystV2(db_path="database/tanakh.db")
micro_analysis, research_bundle = micro_analyst.analyze_psalm(20, macro_analysis)

# Save outputs
logger.info("\nSaving outputs...")

from src.schemas.analysis_schemas import save_analysis
save_analysis(micro_analysis, str(output_dir / "psalm_020_micro_v2_TEST.json"), format="json")

with open(output_dir / "psalm_020_research_v2_TEST.md", 'w', encoding='utf-8') as f:
    f.write(research_bundle.to_markdown())

logger.info(f"✓ Micro analysis saved to {output_dir / 'psalm_020_micro_v2_TEST.json'}")
logger.info(f"✓ Research bundle saved to {output_dir / 'psalm_020_research_v2_TEST.md'}")

# Print summary
summary = research_bundle.to_dict()['summary']
logger.info("\n" + "=" * 80)
logger.info("RESEARCH BUNDLE SUMMARY")
logger.info("=" * 80)
logger.info(f"Lexicon entries: {summary['lexicon_entries']}")
logger.info(f"Concordance searches: {summary['concordance_searches']}")
logger.info(f"Concordance results: {summary['concordance_results']}")
logger.info(f"Figurative searches: {summary['figurative_searches']}")
logger.info(f"Figurative instances: {summary['figurative_instances']}")
logger.info(f"Commentary verses: {summary['commentary_verses']}")
logger.info(f"Commentary entries: {summary['commentary_entries']}")
logger.info("=" * 80)

print("\n✓ Test complete! Check the log output above for detailed research requests.")
