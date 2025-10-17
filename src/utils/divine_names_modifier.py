r"""
Divine Names Modifier for Psalms Commentary
Adapts the Hebrew Divine Names Modifier for use in Psalms commentary generation.

This module modifies Hebrew text to render divine names in non-sacred format,
replacing:
- יהוה → ה׳ (Tetragrammaton)
- אלהים → אלקים (Elohim family)
- אֵל → קֵל (El with tzere)
- צבאות → צבקות (Tzevaot)
- שדי → שקי (Shaddai)
- אלוה → אלוק (Eloah)

Based on: Hebrew Divine Names Modifier from Bible project

Author: Claude (Anthropic)
Date: 2025-10-17
"""

import re
import logging
from typing import Optional


class DivineNamesModifier:
    """Modifies Hebrew divine names to non-sacred format"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def modify_text(self, text: str) -> str:
        """
        Apply all divine name modifications to text (Hebrew or mixed English/Hebrew).

        Args:
            text: Input text containing Hebrew divine names

        Returns:
            Modified text with divine names replaced
        """
        if not text or not isinstance(text, str):
            return text

        modified_text = text

        # Apply modifications in order of specificity (most specific first)
        # 1. Tetragrammaton: יהוה → ה׳
        modified_text = self._modify_tetragrammaton(modified_text)

        # 2. El Shaddai: שַׁדַּי → שַׁקַּי (before general patterns)
        modified_text = self._modify_el_shaddai(modified_text)

        # 3. Elohim family: replace ה with ק in divine names
        modified_text = self._modify_elohim_family(modified_text)

        # 4. El with tzere: אֵל → קֵל (NOT preposition אֶל)
        modified_text = self._modify_el_tzere(modified_text)

        # 5. Tzevaot: צְבָאוֹת → צְבָקוֹת
        modified_text = self._modify_tzevaot(modified_text)

        # 6. Eloah: אֱלוֹהַּ → אֱלוֹקַּ
        modified_text = self._modify_eloah(modified_text)

        # Log if text changed
        if modified_text != text and self.logger:
            self.logger.debug(f"Divine names modified in text")

        return modified_text

    def _modify_tetragrammaton(self, text: str) -> str:
        """Replace יהוה with ה׳"""
        # Match both voweled and unvoweled forms
        patterns = [
            (r'יהוה', 'ה׳'),  # Unvoweled
            (r'יְ?[\u0591-\u05C7]*הֹ?[\u0591-\u05C7]*וָ?[\u0591-\u05C7]*ה', 'ה׳'),  # Voweled with cantillation marks
        ]

        modified = text
        for pattern, replacement in patterns:
            modified = re.sub(pattern, replacement, modified)

        return modified

    def _modify_elohim_family(self, text: str) -> str:
        """Replace ה with ק in Elohim family words"""

        modified = text

        # Pattern 1: Basic unvoweled אלהים
        if 'אלהים' in text:
            modified = modified.replace('אלהים', 'אלקים')

        # Pattern 2: Voweled Elohim patterns with cantillation marks
        elohim_pattern = r'א[\u0591-\u05C7]*[ֱ][\u0591-\u05C7]*ל[\u0591-\u05C7]*[ֹ][\u0591-\u05C7]*ה[\u0591-\u05C7]*[ִֵֶַָ][\u0591-\u05C7]*[םיּךֶָו]'
        def elohim_replacer(match):
            return match.group().replace('ה', 'ק')

        modified = re.sub(elohim_pattern, elohim_replacer, modified)

        # Pattern 2b: Prefixed Elohim forms (וֵאלֹהִים, כֵּאלֹהִים, לֵאלֹהִים, בֵּאלֹהִים, מֵאלֹהִים)
        prefixed_elohim_pattern = r'[ובכלמ][\u0591-\u05C7]*[ִֵֶַּ]?[\u0591-\u05C7]*א[\u0591-\u05C7]*ל[\u0591-\u05C7]*[ֹ][\u0591-\u05C7]*ה[\u0591-\u05C7]*[ִֵֶַָ]'
        modified = re.sub(prefixed_elohim_pattern, elohim_replacer, modified)

        # Pattern 3: With definite article הָאֱלֹהִים
        ha_elohim_pattern = r'ה[\u0591-\u05C7]*[ָ]?[\u0591-\u05C7]*א[\u0591-\u05C7]*[ֱ][\u0591-\u05C7]*ל[\u0591-\u05C7]*[ֹ][\u0591-\u05C7]*ה[\u0591-\u05C7]*[ִֵֶַָ][\u0591-\u05C7]*[םיּךֶָו]'
        modified = re.sub(ha_elohim_pattern, elohim_replacer, modified)

        # Pattern 4: Construct form with vav-holam: אֱלוֹהֵי (Elohei - "God of")
        elohei_construct_pattern = r'א[\u0591-\u05C7]*[ֱ][\u0591-\u05C7]*ל[\u0591-\u05C7]*ו[\u0591-\u05C7]*[ֹ][\u0591-\u05C7]*ה[\u0591-\u05C7]*[ִֵֶַָ]'
        modified = re.sub(elohei_construct_pattern, elohim_replacer, modified)

        return modified

    def _modify_el_tzere(self, text: str) -> str:
        """Replace אֵל (with tzere) with קֵל, but NOT אֶל (with segol)"""
        pattern = r'(^|[\s\-\u05BE])אֵ([\u0591-\u05C7]*)ל(?=[\s\-\u05BE]|$)'

        def replacer(match):
            prefix = match.group(1)
            cantillation = match.group(2)
            return f"{prefix}קֵ{cantillation}ל"

        modified = re.sub(pattern, replacer, text)
        return modified

    def _modify_tzevaot(self, text: str) -> str:
        """Replace א with ק in צְבָאוֹת"""
        # Unvoweled form
        if 'צבאות' in text:
            modified = text.replace('צבאות', 'צבקות')
        else:
            modified = text

        # Voweled form with cantillation marks
        tzevaot_pattern = r'צ[\u0591-\u05C7]*[ְ]?[\u0591-\u05C7]*ב[\u0591-\u05C7]*[ָ]?[\u0591-\u05C7]*א[\u0591-\u05C7]*[וֹ]?[\u0591-\u05C7]*ת'
        def tzevaot_replacer(match):
            return match.group().replace('א', 'ק')

        modified = re.sub(tzevaot_pattern, tzevaot_replacer, modified)
        return modified

    def _modify_el_shaddai(self, text: str) -> str:
        """Replace ד with ק in שַׁדַּי (only when standalone)"""
        modified = text

        # Unvoweled form - only match when preceded/followed by word boundary
        unvoweled_pattern = r'(^|[\s\-\u05BE.,;:!?])שדי(?=[\u0591-\u05C7]*(?:[\s\-\u05BE.,;:!?]|$))'
        def unvoweled_replacer(match):
            prefix = match.group(1)
            return f"{prefix}שקי"

        modified = re.sub(unvoweled_pattern, unvoweled_replacer, modified)

        # Voweled form with cantillation marks - only match standalone word
        shaddai_pattern = r'(^|[\s\-\u05BE.,;:!?])ש[\u0591-\u05C7]*[ַׁ]?[\u0591-\u05C7]*ד[\u0591-\u05C7]*[ַּ]?[\u0591-\u05C7]*י(?=[\u0591-\u05C7]*(?:[\s\-\u05BE.,;:!?]|$))'
        def shaddai_replacer(match):
            prefix = match.group(1)
            modified_word = match.group()[len(prefix):].replace('ד', 'ק')
            return f"{prefix}{modified_word}"

        modified = re.sub(shaddai_pattern, shaddai_replacer, modified)
        return modified

    def _modify_eloah(self, text: str) -> str:
        """Replace ה with ק in אֱלוֹהַּ (Eloah)"""
        # Unvoweled form
        if 'אלוה' in text:
            modified = text.replace('אלוה', 'אלוק')
        else:
            modified = text

        # Voweled form with cantillation marks
        eloah_pattern = r'א[\u0591-\u05C7]*ֱ[\u0591-\u05C7]*ל[\u0591-\u05C7]*ו[\u0591-\u05C7]*ֹ[\u0591-\u05C7]*ה[\u0591-\u05C7]*ַ[\u0591-\u05C7]*'
        def eloah_replacer(match):
            return match.group().replace('ה', 'ק')

        modified = re.sub(eloah_pattern, eloah_replacer, modified)
        return modified

    def has_divine_names(self, text: str) -> bool:
        """Check if text contains any divine names that would be modified"""
        if not text:
            return False

        patterns = [
            r'יהוה',  # Tetragrammaton
            r'אלהים',  # Elohim
            r'(^|[\s\-\u05BE])אֵ[\u0591-\u05C7]*ל(?=[\s\-\u05BE]|$)',  # El
            r'צבאות',  # Tzevaot
            r'(^|[\s\-\u05BE.,;:!?])שדי',  # Shaddai
            r'אלוה',  # Eloah
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                return True

        return False


def modify_divine_names_in_commentary(commentary_text: str, logger=None) -> str:
    """
    Convenience function to modify divine names in commentary text.

    Args:
        commentary_text: Commentary markdown text
        logger: Optional logger instance

    Returns:
        Modified commentary with divine names replaced
    """
    modifier = DivineNamesModifier(logger=logger)
    return modifier.modify_text(commentary_text)
