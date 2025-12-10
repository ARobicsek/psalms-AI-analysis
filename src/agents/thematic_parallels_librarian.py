"""
Thematic Parallels Librarian - Finds thematically similar passages in Tanakh.

This agent uses vector embeddings to find passages in the Tanakh (outside Psalms)
that are thematically similar to psalm verses being analyzed—even when they share
no common vocabulary.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..thematic.embedding_service import create_embedding_service
from ..thematic.vector_store import create_vector_store

logger = logging.getLogger(__name__)


@dataclass
class ThematicParallel:
    """A thematic parallel passage."""
    reference: str  # e.g., "Genesis 1:26-27"
    similarity: float  # 0.0 to 1.0, higher is more similar
    hebrew_text: str  # The Hebrew text of the passage
    book: str  # e.g., "Genesis"
    book_category: str  # e.g., "Torah", "Prophets", "Writings"
    context_verses: int  # Number of verses in the passage


class ThematicParallelsLibrarian:
    """Finds thematic parallels using vector similarity search."""

    def __init__(
        self,
        vector_store_path: str = "data/thematic_corpus/chroma_db",
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-large",
        similarity_threshold: float = 0.4,
        max_results: int = 10,
        exclude_psalms: bool = False,  # Include Psalms by default, filter only exact matches
    ):
        """
        Initialize the Thematic Parallels Librarian.

        Args:
            vector_store_path: Path to ChromaDB vector store
            embedding_provider: Service for generating embeddings
            embedding_model: Model name for embeddings
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of parallels to return
            exclude_psalms: Whether to exclude Psalms from results
        """
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.exclude_psalms = exclude_psalms

        # Initialize embedding service
        self.embedding_service = create_embedding_service(
            provider=embedding_provider,
            model=embedding_model
        )

        # Initialize vector store
        self.vector_store = create_vector_store(
            provider="chroma",
            persist_directory=vector_store_path
        )

        logger.info(f"Initialized ThematicParallelsLibrarian")
        logger.info(f"  Embedding model: {self.embedding_service.model_name}")
        logger.info(f"  Vector store: {vector_store_path}")
        logger.info(f"  Similarity threshold: {similarity_threshold}")
        logger.info(f"  Max results: {max_results}")

    def find_parallels(
        self,
        query_text: str,
        query_verses: Optional[List[str]] = None,
        min_similarity: Optional[float] = None
    ) -> List[ThematicParallel]:
        """
        Find thematic parallels for the given query.

        Args:
            query_text: The text to find parallels for (Hebrew or English)
            query_verses: List of verses being analyzed (for filtering duplicates)
            min_similarity: Override default similarity threshold

        Returns:
            List of ThematicParallel objects sorted by similarity
        """
        if min_similarity is None:
            min_similarity = self.similarity_threshold

        logger.info(f"Finding thematic parallels for query: {query_text[:100]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.get_embedding(query_text)

        # Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=self.max_results * 2  # Get more to filter
        )

        # Convert results to ThematicParallel objects
        parallels = []
        for result in search_results["results"]:
            # Check similarity threshold
            if result["similarity"] < min_similarity:
                continue

            metadata = result["metadata"]

            # Skip Psalms if requested
            if self.exclude_psalms and metadata.get("book") == "Psalms":
                continue

            # Create ThematicParallel object
            parallel = ThematicParallel(
                reference=metadata["reference"],
                similarity=result["similarity"],
                hebrew_text=result["document"],
                book=metadata["book"],
                book_category=metadata["book_category"],
                context_verses=metadata.get("verse_count", 5)
            )

            # Skip if this is one of the query verses
            if query_verses and self._is_duplicate(parallel.reference, query_verses):
                continue

            parallels.append(parallel)

        # Sort by similarity and limit results
        parallels.sort(key=lambda p: p.similarity, reverse=True)
        parallels = parallels[:self.max_results]

        logger.info(f"Found {len(parallels)} thematic parallels")
        return parallels

    def find_parallels_for_psalm_verse(
        self,
        psalm_number: int,
        verse_number: int,
        hebrew_text: str,
        english_text: Optional[str] = None
    ) -> List[ThematicParallel]:
        """
        Find thematic parallels for a specific psalm verse.

        NOTE: This method is deprecated. Use find_parallels_for_psalm_segment instead
        to search with 5-verse windows that match the corpus structure.

        Args:
            psalm_number: Psalm number
            verse_number: Verse number within the psalm
            hebrew_text: Hebrew text of the verse
            english_text: English translation (optional - not used for search)

        Returns:
            List of ThematicParallel objects
        """
        # Use Hebrew only for search (corpus contains only Hebrew)
        query_text = hebrew_text

        # Build query verses list for filtering
        query_verses = [f"Psalms {psalm_number}:{verse_number}"]

        return self.find_parallels(query_text, query_verses)

    def find_parallels_for_psalm_segment(
        self,
        psalm_number: int,
        start_verse: int,
        end_verse: int,
        hebrew_text: str,
        english_text: Optional[str] = None
    ) -> List[ThematicParallel]:
        """
        Find thematic parallels for a segment of psalm verses.

        Args:
            psalm_number: Psalm number
            start_verse: Starting verse number
            end_verse: Ending verse number
            hebrew_text: Hebrew text of the segment
            english_text: English translation (optional - not used for search)

        Returns:
            List of ThematicParallel objects
        """
        # Use Hebrew only for search (corpus contains only Hebrew)
        query_text = hebrew_text

        # Build query verses list for filtering
        query_verses = []
        for v in range(start_verse, end_verse + 1):
            query_verses.append(f"Psalms {psalm_number}:{v}")

        return self.find_parallels(query_text, query_verses)

    def find_parallels_for_psalm_with_windowing(
        self,
        psalm_number: int,
        verses: List[Dict[str, str]],  # List of {'verse': int, 'hebrew': str, 'english': str}
        window_size: int = 5,
        window_overlap: int = 4
    ) -> List[ThematicParallel]:
        """
        Find thematic parallels using 5-verse windows that match the corpus structure.

        This is the recommended method for finding parallels as it uses the same
        chunking strategy as the vector index (5-verse overlapping windows).

        Args:
            psalm_number: Psalm number
            verses: List of verses with their texts
            window_size: Number of verses per window (default: 5)
            window_overlap: Overlap between windows (default: 4)

        Returns:
            List of ThematicParallel objects (deduplicated by reference)
        """
        logger.info(f"Finding parallels for Psalm {psalm_number} using {len(verses)} verses")
        logger.info(f"Window size: {window_size}, Overlap: {window_overlap}")

        all_parallels = []
        windows_processed = 0

        # Create sliding windows
        for i in range(0, len(verses), window_size - window_overlap):
            window_end = min(i + window_size, len(verses))

            if window_end - i < window_size and i > 0:
                # Skip windows that are too small unless it's the first one
                continue

            window_verses = verses[i:window_end]
            window_verses_list = [f"Psalms {psalm_number}:{v['verse']}" for v in window_verses]

            # Combine Hebrew text from all verses in window
            window_hebrew = " ".join(v['hebrew'] for v in window_verses)

            windows_processed += 1
            logger.info(f"Processing window {windows_processed}: verses {window_verses[0]['verse']}-{window_verses[-1]['verse']}")

            # Find parallels for this window
            window_parallels = self.find_parallels(window_hebrew, window_verses_list)

            # Add window info to each parallel
            for parallel in window_parallels:
                parallel._psalm_window_verses = f"{window_verses[0]['verse']}-{window_verses[-1]['verse']}"

            all_parallels.extend(window_parallels)

        # Deduplicate by reference (keep highest similarity)
        unique_parallels = {}
        for parallel in all_parallels:
            if parallel.reference not in unique_parallels or parallel.similarity > unique_parallels[parallel.reference].similarity:
                unique_parallels[parallel.reference] = parallel

        # Sort by similarity
        result = sorted(unique_parallels.values(), key=lambda p: p.similarity, reverse=True)

        logger.info(f"Processed {windows_processed} windows, found {len(result)} unique parallels")
        return result

    def _is_duplicate(self, reference: str, query_verses: List[str]) -> bool:
        """
        Check if a result reference overlaps with the query verses.

        Args:
            reference: Reference string like "Genesis 1:1-5"
            query_verses: List of query verse references

        Returns:
            True if this reference overlaps with query verses
        """
        # Normalize book names (Psalm/Psalms)
        normalized_ref = reference.replace("Psalms", "Psalm")

        for query_verse in query_verses:
            normalized_query = query_verse.replace("Psalms", "Psalm")

            # Check for overlap with verse ranges
            if normalized_query in normalized_ref or normalized_ref in normalized_query:
                return True

            # Check for verse range overlap (e.g., Psalm 23:1 overlaps with Psalm 23:1-5)
            if self._verses_overlap(normalized_query, normalized_ref):
                return True

        return False

    def _verses_overlap(self, ref1: str, ref2: str) -> bool:
        """
        Check if two verse references overlap.

        Args:
            ref1: First reference (e.g., "Psalm 23:1")
            ref2: Second reference (e.g., "Psalm 23:1-5")

        Returns:
            True if the verse ranges overlap
        """
        # Extract book, chapter, and verses
        import re

        # Pattern to match book chapter:verse(s)
        pattern = r"(.*?)(\d+):(\d+)(?:-(\d+))?"

        m1 = re.match(pattern, ref1)
        m2 = re.match(pattern, ref2)

        if not m1 or not m2:
            return False

        book1, chapter1, verse1_start, verse1_end = m1.groups()
        book2, chapter2, verse2_start, verse2_end = m2.groups()

        # Normalize single verses to have same start/end
        verse1_end = verse1_end or verse1_start
        verse2_end = verse2_end or verse2_start

        # Convert to integers
        chapter1 = int(chapter1)
        chapter2 = int(chapter2)
        verse1_start = int(verse1_start)
        verse1_end = int(verse1_end)
        verse2_start = int(verse2_start)
        verse2_end = int(verse2_end)

        # Check if same book and chapter
        if book1 != book2 or chapter1 != chapter2:
            return False

        # Check if verse ranges overlap
        return not (verse1_end < verse2_start or verse2_end < verse1_start)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_chunks": self.vector_store.count() if hasattr(self.vector_store, "count") else "unknown",
            "embedding_model": self.embedding_service.model_name,
            "embedding_dimension": self.embedding_service.dimension,
            "similarity_threshold": self.similarity_threshold,
            "max_results": self.max_results,
        }
        return stats


def create_thematic_librarian(**kwargs) -> ThematicParallelsLibrarian:
    """
    Factory function to create a ThematicParallelsLibrarian instance.

    Args:
        **kwargs: Arguments passed to ThematicParallelsLibrarian constructor

    Returns:
        ThematicParallelsLibrarian instance
    """
    return ThematicParallelsLibrarian(**kwargs)