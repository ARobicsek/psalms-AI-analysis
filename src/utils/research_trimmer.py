"""
Research Trimmer Utility

Intelligently trims research bundles to fit within token limits while preserving
high-value interpretive content.

Shared by SynthesisWriter and InsightExtractor.

Author: Claude (Anthropic)
Date: 2026-01-26
"""

import re
from typing import Tuple, List, Optional
from src.utils.logger import get_logger

class ResearchTrimmer:
    """
    Utility for trimming research bundles to specific character limits.
    """
    
    def __init__(self, logger=None):
        """Initialize with optional logger."""
        self.logger = logger or get_logger("research_trimmer")
        self._sections_removed = []
        
    @property
    def sections_removed(self) -> List[str]:
        """Return list of sections removed during last trim operation."""
        return self._sections_removed

    def trim_bundle(self, research_bundle: str, max_chars: int = 400000) -> Tuple[str, bool, bool]:
        """
        Intelligently trim research bundle to fit within token limits.

        Priority order for trimming (first to last - least to most important):
        1. Related Psalms section - progressive trim (remove full psalm texts first)
        2. Related Psalms section - full removal
        3. Figurative Language - trim to 75%
        4. Figurative Language - trim to 50%

        If still over limit after step 4, return a flag indicating Gemini fallback needed.

        Args:
            research_bundle: Full research bundle markdown
            max_chars: Maximum characters allowed
            
        Returns:
            Tuple of (trimmed_bundle, deep_research_was_removed, needs_gemini_fallback)
        """
        self._sections_removed = []
        deep_research_removed = False
        needs_gemini_fallback = False
        original_size = len(research_bundle)
        
        if original_size <= max_chars:
            return research_bundle, deep_research_removed, needs_gemini_fallback
            
        self.logger.warning(f"Research bundle too large ({original_size:,} chars). Max: {max_chars:,}. Starting progressive trimming...")
        
        # ========================================
        # STEP 1: Trim Related Psalms (remove full texts, keep relationships)
        # ========================================
        related_section, temp_bundle = self._extract_section(research_bundle, 'Related Psalms')
        
        if related_section:
            trimmed_related = self._trim_related_psalms(related_section)
            test_bundle = temp_bundle + '\n\n' + trimmed_related
            
            if len(test_bundle) <= max_chars:
                self.logger.info(f"Trimmed Related Psalms (removed full texts). Size: {original_size:,} -> {len(test_bundle):,} chars")
                return self._finalize_bundle(test_bundle, original_size, ["Related Psalms (full texts removed)"]), False, False
            else:
                # Still over - continue with this as base
                research_bundle = test_bundle
                self._sections_removed.append("Related Psalms (full texts removed)")
                
        # ========================================
        # STEP 2: Remove Related Psalms entirely
        # ========================================
        current_len = len(research_bundle)
        if current_len > max_chars:
            # We need to re-extract because bundle might have changed in step 1
            # Or if step 1 didn't solve it, we might want to remove the whole section
            related_section, temp_bundle = self._extract_section(research_bundle, 'Related Psalms')
            
            if related_section:
                research_bundle = temp_bundle
                if "Related Psalms (full texts removed)" in self._sections_removed:
                    self._sections_removed.remove("Related Psalms (full texts removed)")
                self._sections_removed.append("Related Psalms")
                
                if len(research_bundle) <= max_chars:
                    self.logger.info(f"Removed Related Psalms entirely. Size: {original_size:,} -> {len(research_bundle):,} chars")
                    return self._finalize_bundle(research_bundle, original_size, self._sections_removed), False, False
                    
        # ========================================
        # STEP 3: Trim Figurative Language to 75%
        # ========================================
        current_len = len(research_bundle)
        if current_len > max_chars:
            figurative_section, temp_bundle = self._extract_section(research_bundle, 'Figurative Language')
            
            if figurative_section:
                is_curator_output = '(Curated)' in figurative_section or 'Curated Insights' in figurative_section
                
                if is_curator_output:
                    self.logger.info("Figurative Language is curated output - skipping trimming")
                else:
                    trimmed_fig = self._trim_figurative_by_ratio(figurative_section, 0.75)
                    test_bundle = temp_bundle + '\n\n' + trimmed_fig
                    
                    if len(test_bundle) <= max_chars:
                        self.logger.info(f"Trimmed Figurative Language to 75%. Size: {original_size:,} -> {len(test_bundle):,} chars")
                        return self._finalize_bundle(test_bundle, original_size, self._sections_removed + ["Figurative Language (trimmed to 75%)"]), False, False
                    else:
                        research_bundle = test_bundle
                        self._sections_removed.append("Figurative Language (trimmed to 75%)")

        # ========================================
        # STEP 4: Trim Figurative Language to 50%
        # ========================================
        current_len = len(research_bundle)
        if current_len > max_chars:
            figurative_section, temp_bundle = self._extract_section(research_bundle, 'Figurative Language')
            
            if figurative_section:
                is_curator_output = '(Curated)' in figurative_section or 'Curated Insights' in figurative_section
                
                if not is_curator_output:
                    trimmed_fig = self._trim_figurative_by_ratio(figurative_section, 0.50)
                    research_bundle = temp_bundle + '\n\n' + trimmed_fig
                    
                    if "Figurative Language (trimmed to 75%)" in self._sections_removed:
                        self._sections_removed.remove("Figurative Language (trimmed to 75%)")
                    self._sections_removed.append("Figurative Language (trimmed to 50%)")
                    
                    if len(research_bundle) <= max_chars:
                        self.logger.info(f"Trimmed Figurative Language to 50%. Size: {original_size:,} -> {len(research_bundle):,} chars")
                        return self._finalize_bundle(research_bundle, original_size, self._sections_removed), False, False

        # ========================================
        # STEP 5: Check Deep Web Research
        # ========================================
        # If still over limit, removing Deep Research is a last resort option, 
        # but typically we prefer Gemini fallback for massive contexts.
        # However, if we MUST fit (e.g. for Insight Extractor which has strict limit),
        # we might need to be more aggressive. For now, we flag for Gemini fallback.
        
        current_len = len(research_bundle)
        if current_len > max_chars:
            # Check if Deep Research is huge and could save us
            deep_section, _ = self._extract_section(research_bundle, 'Deep Web Research')
            if deep_section and len(deep_section) > 5000:
                # Only remove if it's substantial and would actually help
                pass # Currently decision is to fallback to Gemini rather than lose deep research

            needs_gemini_fallback = True
            self.logger.warning(f"Bundle still {current_len:,} chars (limit: {max_chars:,}). Flagging for Gemini fallback.")

        return self._finalize_bundle(research_bundle, original_size, self._sections_removed), deep_research_removed, needs_gemini_fallback

    def _finalize_bundle(self, bundle: str, original_size: int, sections_removed: List[str]) -> str:
        """Add summary footer to bundle."""
        trimming_summary = f"\n\n---\n## Research Bundle Processing Summary\n"
        trimming_summary += f"- Original size: {original_size:,} characters\n"
        trimming_summary += f"- Final size: {len(bundle):,} characters\n"
        trimming_summary += f"- Removed: {original_size - len(bundle):,} characters ({((original_size - len(bundle)) / original_size * 100):.1f}%)\n"
        
        if sections_removed:
            trimming_summary += f"- Sections removed/trimmed: {', '.join(sections_removed)}\n"
            
        return bundle + trimming_summary

    def _extract_section(self, bundle: str, section_pattern: str) -> Tuple[str, str]:
        """Extract a section from the bundle, return (section_content, bundle_without_section)."""
        pattern = rf'(## {section_pattern}.*?)(?=\n## [A-Z]|\n---\n\n## |\Z)'
        match = re.search(pattern, bundle, flags=re.DOTALL)
        if match:
            section = match.group(1)
            bundle_without = bundle[:match.start()] + bundle[match.end():]
            return section.strip(), bundle_without
        return "", bundle

    def _trim_related_psalms(self, section: str) -> str:
        """Trim Related Psalms section by removing full psalm text blocks."""
        if not section:
            return section
            
        full_text_pattern = r'### Full Text of Psalm \d+.*?(?=### (?:Full Text|Shared|Related)|## |$)'
        trimmed = re.sub(full_text_pattern, '', section, flags=re.DOTALL)
        
        if len(trimmed) < len(section):
            trimmed += "\n\n*[Full psalm texts removed for context length - word/phrase relationships preserved]*\n"
            
        return trimmed

    def _trim_figurative_by_ratio(self, section: str, keep_ratio: float) -> str:
        """Trim figurative language section, prioritizing instances from Psalms."""
        if not section or keep_ratio >= 1.0:
            return section

        # Split into query blocks
        query_pattern = r'(### Query \d+.*?)(?=### Query \d+|$)'
        queries = re.findall(query_pattern, section, re.DOTALL)

        if not queries:
            # Fallback: simple line-based trimming
            lines = section.split('\n')
            header_lines = []
            content_lines = []
            in_header = True
            for line in lines:
                if in_header and (line.startswith('##') or line.startswith('*') or line.strip() == ''):
                    header_lines.append(line)
                else:
                    in_header = False
                    content_lines.append(line)
            keep_count = max(1, int(len(content_lines) * keep_ratio))
            trimmed_content = content_lines[:keep_count]
            trimmed_content.append(f"\n[Section trimmed to {keep_ratio:.0%} for context length]")
            return '\n'.join(header_lines + trimmed_content)

        trimmed_queries = []
        for query_block in queries:
            match = re.match(r'(.*?#### (?:Instances|All Instances).*?:)(.*)', query_block, re.DOTALL)
            if not match:
                trimmed_queries.append(query_block)
                continue

            header = match.group(1)
            instances_text = match.group(2)
            
            instance_pattern = r'(\*\*[^*]+\*\*.*?)(?=\*\*[^*]+\*\*|$)'
            instances = re.findall(instance_pattern, instances_text, re.DOTALL)

            if not instances:
                trimmed_queries.append(query_block)
                continue

            # Prioritize Psalms
            psalms_instances = [inst for inst in instances if "Psalms" in inst]
            other_instances = [inst for inst in instances if "Psalms" not in inst]
            
            target_count = max(1, int(len(instances) * keep_ratio))
            
            kept_instances = []
            if len(psalms_instances) >= target_count:
                kept_instances = psalms_instances[:target_count]
            else:
                kept_instances.extend(psalms_instances)
                remaining = target_count - len(psalms_instances)
                if remaining > 0:
                    kept_instances.extend(other_instances[:remaining])
            
            omitted = len(instances) - len(kept_instances)
            trimmed_block = header + '\n' + ''.join(kept_instances)
            if omitted > 0:
                trimmed_block += f"\n\n[{omitted} more instances omitted for space]\n"

            trimmed_queries.append(trimmed_block)

        result = '## Figurative Language Instances\n\n' + '\n'.join(trimmed_queries)
        return result
