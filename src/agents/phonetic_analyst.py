"""
This module defines the PhoneticAnalyst agent, which is responsible for
transcribing Hebrew text into a detailed phonetic and syllabic structure
based on reconstructed Biblical Hebrew phonology.
"""

import unicodedata2 as unicodedata

class PhoneticAnalyst:
    """
    An agent that analyzes Hebrew text and produces a phonetic transcription.
    """

    def __init__(self):
        """
        Initializes the PhoneticAnalyst with mappings based on the reference guide.
        """
        self.consonant_map = {
            'א': "'", 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'w', 'ז': 'z',
            'ח': 'kh', 'ט': 't', 'י': 'y', 'כ': 'k', 'ך': 'kh', 'ל': 'l', 'מ': 'm',
            'ם': 'm', 'נ': 'n', 'ן': 'n', 'ס': 's', 'ע': 'ʿ', 'פ': 'p', 'ף': 'f',
            'צ': 'ts', 'ץ': 'ts', 'ק': 'q', 'ר': 'r', 'ש': 'sh', 'ת': 't'
        }
        self.vowel_map = {
            'ַ': 'a',  # Patah (U+05B7)
            'ָ': 'ā',  # Qamets Gadol (U+05B8)
            'ֵ': 'ē',  # Tsere (U+05B5)
            'ֶ': 'e',  # Segol (U+05B6)
            'ִ': 'i',  # Hiriq (U+05B4)
            'ֹ': 'ō',  # Holam (U+05B9)
            'ֺ': 'ō',  # Holam Haser for Vav (U+05BA)
            'ֻ': 'u',  # Qubuts (U+05BB)
            'ְ': 'ə',  # Shewa (U+05B0)
            'ֲ': 'a',  # Hataf Patah (U+05B2)
            'ֱ': 'e',  # Hataf Segol (U+05B1)
            'ֳ': 'o',  # Hataf Qamets (U+05B3)
            'ׇ': 'o'   # Qamets Qatan (U+05C7) - short 'o' not long 'ā'
            # NOTE: Dagesh (U+05BC ּ) is NOT a vowel - removed from this map
        }
        self.begadkefat_soft = {
            'ב': 'v', 'ג': 'gh', 'ד': 'dh', 'כ': 'kh', 'פ': 'f', 'ת': 'th'
        }
        # Cantillation marks with stress levels
        self.cantillation_stress = {
            # Primary stress (level 2) - major disjunctive accents
            '\u05BD': 2,  # Silluq/Meteg
            '\u0591': 2,  # Atnah
            '\u0594': 2,  # Zaqef Qaton
            '\u0595': 2,  # Zaqef Gadol
            '\u0596': 2,  # Tifcha
            '\u0597': 2,  # R'vi'i (Revia)
            '\u0598': 2,  # Zarqa
            '\u0599': 2,  # Pashta
            '\u059A': 2,  # Yetiv
            '\u059B': 2,  # Tevir
            '\u05A0': 2,  # Telisha Gedola
            '\u05A9': 2,  # Telisha Qetana
            '\u0593': 2,  # Shalshelet
            '\u059C': 2,  # Geresh
            '\u059D': 2,  # Geresh Muqdam
            '\u059E': 2,  # Gershayim

            # Secondary stress (level 1) - conjunctive accents
            # Note: Dehi (֭ U+05AD) NOT included - it's a conjunctive accent that
            # doesn't mark lexical stress (e.g., הָ֭אָדָם has stress on final syllable)
            '\u05A3': 1,  # Munach
            '\u05A4': 1,  # Mahpakh
            '\u05A5': 1,  # Mercha
            '\u05A8': 1,  # Qadma
            '\u05AB': 1,  # Ole
            '\u05A1': 1,  # Pazer
            '\u05A7': 1,  # Darga
            '\u05AA': 1,  # Galgal
            '\u05AC': 1,  # Iluy
        }
        # Unicode characters
        self.dagesh = '\u05BC'
        self.shin_dot = '\u05C1'
        self.sin_dot = '\u05C2'
        self.qamets = '\u05B8'
        self.patah = '\u05B7'
        self.shewa = '\u05B0'

    def transcribe_verse(self, hebrew_verse: str) -> dict:
        """
        Transcribes a full Hebrew verse into a structured phonetic format.
        Handles ketiv-qere notation: (ketiv) [qere] - only transcribes the qere.
        """
        # Normalize to handle composite characters
        normalized_verse = unicodedata.normalize('NFD', hebrew_verse)

        # Handle ketiv-qere: remove (ketiv) and unwrap [qere]
        # Pattern: (text) [text] -> keep only the bracketed text
        import re
        # Remove parenthetical ketiv (what is written but not read)
        normalized_verse = re.sub(r'\([^)]*\)\s*', '', normalized_verse)
        # Unwrap bracketed qere (what is read)
        normalized_verse = re.sub(r'\[([^\]]*)\]', r'\1', normalized_verse)

        words = normalized_verse.split()

        analysis = {
            "original_text": hebrew_verse,
            "words": [self._transcribe_word(word) for word in words]
        }
        return analysis

    def _transcribe_word(self, hebrew_word: str) -> dict:
        """
        Transcribes a single Hebrew word.
        This is a complex process involving context-sensitive rules.
        Now includes stress detection from cantillation marks.

        When multiple cantillation marks are present, the LAST (rightmost) one
        typically indicates the actual stress position.

        Maqqef compounds (word1־word2) are handled specially: each component
        gets its own stress, since they are separate phonological words.
        """
        # Check for maqqef compounds
        if '־' in hebrew_word:
            return self._transcribe_maqqef_compound(hebrew_word)
        phonemes = []
        transcription = []
        stressed_phoneme_index = None  # Track which phoneme position has stress
        stress_level = 0  # 0=unstressed, 1=secondary, 2=primary

        chars = list(hebrew_word)
        i = 0
        while i < len(chars):
            char = chars[i]
            
            # --- Consonant Logic ---
            if char in self.consonant_map:
                # Look ahead for dagesh, shin/sin dots, vowels, and cantillation marks
                j = i + 1
                modifiers = []
                has_cantillation = False
                cantillation_level = 0

                while j < len(chars) and unicodedata.category(chars[j]) == 'Mn':
                    modifiers.append(chars[j])
                    # Check for cantillation marks (stress indicators)
                    if chars[j] in self.cantillation_stress:
                        has_cantillation = True
                        # If multiple cantillation marks, use the highest level
                        cantillation_level = max(cantillation_level, self.cantillation_stress[chars[j]])
                    j += 1

                # If this consonant has a cantillation mark, it marks the stressed syllable
                # We'll mark the VOWEL following this consonant as stressed (since stress is on the syllable)
                # When multiple marks present, prefer rightmost (later in word) with same or higher level
                if has_cantillation and cantillation_level >= stress_level:
                    # Mark the position where we'll add the vowel (current phoneme count + 1 for consonant + 1 for vowel)
                    stressed_phoneme_index = len(phonemes) + 1  # Will point to the vowel
                    stress_level = cantillation_level

                # === EXISTING: Check if vav is serving as mater lectionis ===
                if char == 'ו':
                    # Check for holam (ֹ or ֺ) - vav is vowel marker
                    if '\u05B9' in modifiers or '\u05BA' in modifiers:
                        # This is holam male (וֹ) - just transcribe as 'ō'
                        phonemes.append('ō')
                        transcription.append('ō')
                        i = j
                        continue  # Skip consonant processing
                    
                    # Check for shureq (וּ with dagesh)
                    if '\u05BC' in modifiers:
                        # This is shureq - just transcribe as 'ū'
                        phonemes.append('ū')
                        transcription.append('ū')
                        i = j
                        continue  # Skip consonant processing
                
                # === EXISTING: Begadkefat and dagesh detection ===
                is_begadkefat = char in self.begadkefat_soft
                has_dagesh = self.dagesh in modifiers
                
                # Determine consonant sound
                consonant_sound = self.consonant_map[char]
                
                # Shin/Sin differentiation
                if char == 'ש':
                    if self.sin_dot in modifiers:
                        consonant_sound = 's'
                    # Default is 'sh', so no change needed for shin_dot
                
                # Begadkefat softening (simple version: assume soft unless dagesh)
                if is_begadkefat and not has_dagesh:
                    consonant_sound = self.begadkefat_soft[char]

                # === NEW: Dagesh Forte (Gemination) Detection ===
                is_geminated = False
                if has_dagesh:
                    # Determine if this is dagesh forte (gemination) vs. dagesh lene (hardening)
                    
                    if not is_begadkefat:
                        # Non-begadkefat letters: dagesh is ALWAYS forte (gemination)
                        # Examples: נּ in חַנּוּן, לּ in הַלְלוּיָהּ
                        is_geminated = True
                    else:
                        # Begadkefat letters: dagesh could be lene OR forte
                        # Heuristic: If preceded by a vowel (not beginning of word), 
                        # it's likely forte (gemination)
                        
                        # Check if there was a vowel before this consonant
                        if i > 0:
                            # Look back for a vowel in previous modifiers
                            prev_had_vowel = False
                            k = i - 1
                            while k >= 0 and unicodedata.category(chars[k]) == 'Mn':
                                if chars[k] in self.vowel_map:
                                    prev_had_vowel = True
                                    break
                                k -= 1
                            
                            # If previous consonant had a vowel, this dagesh is likely forte
                            if prev_had_vowel and k >= 0 and chars[k] in self.consonant_map:
                                is_geminated = True
                        
                        # Exception: Word-initial position is always dagesh lene (hard)
                        if i == 0:
                            is_geminated = False

                phonemes.append(consonant_sound)
                transcription.append(consonant_sound)
                
                # === NEW: If geminated, add the consonant again ===
                if is_geminated:
                    phonemes.append(consonant_sound)
                    transcription.append(consonant_sound)

                # --- Vowel Logic ---
                vowel_sound = ""
                for mod in modifiers:
                    if mod in self.vowel_map:
                        vowel_sound = self.vowel_map[mod]
                        break # Take the first vowel found
                
                if vowel_sound:
                    # Special case: Qamets He (ָה) at the end of a word is 'āh'
                    is_qamets_he = (vowel_sound == 'ā' and 
                                    i + len(modifiers) + 1 < len(chars) and 
                                    chars[i + len(modifiers) + 1] == 'ה' and
                                    i + len(modifiers) + 2 == len(chars))

                    if not (vowel_sound == 'ə' and not self._is_vocal_shewa(i, chars)):
                         phonemes.append(vowel_sound)
                         transcription.append(vowel_sound)

                i = j # Move index past the processed modifiers
            else:
                # Handle non-consonant characters if any (e.g., maqqef)
                if char == '־':
                    transcription.append('-')
                i += 1

        # Syllabify the phonemes
        syllables = self._syllabify(phonemes)
        syllable_string = self._format_syllables(syllables)

        # Determine which syllable is stressed based on stressed_phoneme_index
        stressed_syllable_index = None
        if stressed_phoneme_index is not None:
            stressed_syllable_index = self._find_syllable_for_phoneme(syllables, stressed_phoneme_index)
        elif len(syllables) > 0 and stress_level == 0:
            # Default Hebrew stress rule: ultima (final syllable)
            # Apply this ONLY when no cantillation mark was found
            stressed_syllable_index = len(syllables) - 1
            stress_level = 1  # Mark as implicit stress (not from cantillation)

        # Format with stress marking
        stressed_syllable_string = self._format_syllables_with_stress(syllables, stressed_syllable_index)

        return {
            "word": unicodedata.normalize('NFC', hebrew_word),
            "transcription": "".join(transcription),
            "syllables": syllables,  # List of syllables (each is list of phonemes)
            "syllable_transcription": syllable_string,  # Hyphenated string (e.g., "tə-hil-lāh")
            "syllable_transcription_stressed": stressed_syllable_string,  # With stress marking
            "stressed_syllable_index": stressed_syllable_index,  # Which syllable is stressed (0-indexed)
            "stress_level": stress_level,  # 0=unstressed, 1=secondary, 2=primary
            "phonemes": phonemes
        }

    def _transcribe_maqqef_compound(self, hebrew_word: str) -> dict:
        """
        Transcribe a maqqef compound (e.g., לְכׇל־הַנֹּפְלִ֑ים).

        Maqqef (־) creates ONE ACCENT DOMAIN. Only the LAST word in the domain
        receives the main stress/accent mark. Earlier words are unstressed.

        This matches Hebrew cantillation rules where maqqef-connected words
        form a single prosodic unit with stress only on the final component.

        Args:
            hebrew_word: Hebrew word containing maqqef (־)

        Returns:
            Combined transcription with stress ONLY on the last component
        """
        # Split by maqqef
        components = hebrew_word.split('־')

        # Recursively transcribe each component (without maqqef)
        component_results = []
        all_syllables = []
        last_component_stress_index = None  # Only track stress from LAST component
        last_component_stress_level = 0

        for i, component in enumerate(components):
            if not component:  # Skip empty strings
                continue

            # Recursively call _transcribe_word (won't have maqqef anymore)
            result = self._transcribe_word(component)
            component_results.append(result)

            # Track syllable positions
            syllable_offset = len(all_syllables)
            all_syllables.extend(result['syllables'])

            # ONLY track stress from the LAST component (maqqef = one accent domain)
            is_last_component = (i == len(components) - 1)
            if is_last_component and result['stressed_syllable_index'] is not None:
                last_component_stress_index = syllable_offset + result['stressed_syllable_index']
                last_component_stress_level = result['stress_level']

        # Combine transcriptions
        combined_transcription = '-'.join([r.get('syllable_transcription', '') for r in component_results])

        # Format with stress ONLY on last component
        if last_component_stress_index is not None:
            combined_stressed = self._format_syllables_with_stress(
                all_syllables,
                last_component_stress_index
            )
        else:
            combined_stressed = combined_transcription

        return {
            "word": unicodedata.normalize('NFC', hebrew_word),
            "transcription": combined_transcription.replace('-', ''),
            "syllables": all_syllables,
            "syllable_transcription": combined_transcription,
            "syllable_transcription_stressed": combined_stressed,
            "stressed_syllable_index": last_component_stress_index,  # Only last component
            "stress_level": last_component_stress_level,
            "phonemes": [p for syl in all_syllables for p in syl]  # Flatten
        }

    def _is_vocal_shewa(self, index, chars):
        """
        Determines if a shewa is vocal based on phonological rules.
        This is a more robust implementation.
        """
        # 1. Shewa under the first letter of a word is vocal.
        if index == 0:
            return True

        # Find the preceding character that is a consonant
        prev_consonant_idx = -1
        for i in range(index - 1, -1, -1):
            if chars[i] in self.consonant_map:
                prev_consonant_idx = i
                break
        
        if prev_consonant_idx == -1:
            return True # Should not happen in a well-formed word

        # Find the vowel associated with the preceding consonant
        prev_vowel = None
        for i in range(prev_consonant_idx + 1, index):
            if chars[i] in self.vowel_map:
                prev_vowel = chars[i]
                break
        
        if prev_vowel is None:
            # 2. Shewa after a consonant with no vowel (beginning of cluster) is vocal.
            return True

        # 3. Shewa after a short vowel is silent.
        # Short vowels are Patah, Segol, Hiriq, Qubuts.
        short_vowels = ['\u05B7', '\u05B6', '\u05B4', '\u05BB']
        if prev_vowel in short_vowels:
            return False

        # 4. Shewa under a consonant with dagesh forte is vocal.
        # (This is complex to check perfectly, but we can approximate)
        # Let's check if the current consonant has a dagesh.
        has_dagesh = False
        for i in range(index + 1, len(chars)):
            if unicodedata.category(chars[i]) != 'Mn':
                break
            if chars[i] == self.dagesh:
                has_dagesh = True
                break
        if has_dagesh:
            # This is tricky. A dagesh could be lene.
            # A simple rule: if it's a begadkefat letter, assume dagesh lene unless geminated.
            # For now, let's assume dagesh in a non-begadkefat implies forte.
            if chars[index] not in self.begadkefat_soft:
                 return True

        # 5. Shewa after a long vowel is vocal.
        # Long vowels are Qamets, Tsere, Holam.
        long_vowels = ['\u05B8', '\u05B5', '\u05B9', '\u05BA']
        if prev_vowel in long_vowels:
            return True
            
        # Default to silent if no other rule applies.
        return False

    def _syllabify(self, phonemes: list) -> list:
        """
        Divide phonemes into syllables following Biblical Hebrew phonology rules.
        
        Rules (based on Gesenius' Hebrew Grammar §26-27):
        1. Every syllable has exactly one vowel (nucleus)
        2. Every syllable begins with a consonant (onset) - except word-initial vowels
        3. Open syllables (CV) are preferred over closed (CVC)
        4. Geminated consonants split across syllable boundary (VC̩-CV)
        5. Word-final consonants close the final syllable
        
        Args:
            phonemes: List of phonemes from transcription
            
        Returns:
            List of syllables (each syllable is a list of phonemes)
        """
        if not phonemes:
            return []
        
        # Define what counts as a vowel
        vowels = {'a', 'ā', 'e', 'ē', 'i', 'ī', 'o', 'ō', 'u', 'ū', 'ə'}
        
        syllables = []
        current_syllable = []
        i = 0
        
        while i < len(phonemes):
            phoneme = phonemes[i]
            
            # Add phoneme to current syllable
            current_syllable.append(phoneme)
            
            # Check if this is a vowel (syllable nucleus)
            if phoneme in vowels:
                # We have a nucleus. Now determine syllable boundary.
                
                # Look ahead to see what comes next
                if i + 1 < len(phonemes):
                    next_phoneme = phonemes[i + 1]
                    
                    # Case 1: Next is a vowel → close syllable (shouldn't happen in well-formed Hebrew)
                    if next_phoneme in vowels:
                        syllables.append(current_syllable)
                        current_syllable = []
                        i += 1
                        continue
                    
                    # Case 2: Next is a consonant
                    # Check if it's followed by another consonant (consonant cluster)
                    if i + 2 < len(phonemes):
                        next_next = phonemes[i + 2]

                        # Case 2a: Gemination (same consonant twice)
                        if next_phoneme == next_next:
                            # Geminated consonant: split across boundary
                            # Add first half to current syllable (closes it)
                            current_syllable.append(next_phoneme)
                            syllables.append(current_syllable)
                            current_syllable = [next_next]  # Start next syllable with second half
                            i += 3  # Skip both consonants
                            continue

                        # Case 2b: Consonant cluster (different consonants)
                        # Check what follows the cluster
                        if next_next in vowels:
                            # CC followed by V: divide before the cluster (CV-CCV)
                            # Exception: If current vowel is shewa (ə), prefer to close the syllable
                            # This handles cases like בְּכׇל (bə-khol not bəkh-ol)
                            if phoneme == 'ə':
                                # Close syllable with shewa, start new syllable with consonant cluster
                                syllables.append(current_syllable)
                                current_syllable = []
                                i += 1
                                continue
                            else:
                                # Non-shewa vowel: keep syllable open (CV-CCV)
                                syllables.append(current_syllable)
                                current_syllable = []
                                i += 1
                                continue
                        else:
                            # CC followed by C or end: close syllable with first C (CVC-C...)
                            current_syllable.append(next_phoneme)
                            syllables.append(current_syllable)
                            current_syllable = []
                            i += 2
                            continue
                    
                    # Case 2c: Single consonant at end of word
                    else:
                        # Consonant at word end: add to current syllable (closes it)
                        current_syllable.append(next_phoneme)
                        syllables.append(current_syllable)
                        current_syllable = []
                        i += 2
                        continue
                
                # Case 3: Vowel at end of word (open syllable)
                else:
                    syllables.append(current_syllable)
                    current_syllable = []
                    i += 1
                    continue
            
            # If we're here, current phoneme is a consonant without vowel yet
            # Continue to next iteration
            i += 1
        
        # Handle any remaining phonemes (shouldn't normally happen in well-formed words)
        if current_syllable:
            syllables.append(current_syllable)
        
        return syllables


    def _format_syllables(self, syllables: list) -> str:
        """
        Format syllables list into hyphen-separated string.

        Args:
            syllables: List of syllables (each syllable is a list of phonemes)

        Returns:
            Hyphen-separated string (e.g., "tə-hil-lāh")
        """
        syllable_strings = [''.join(syl) for syl in syllables]
        return '-'.join(syllable_strings)

    def _find_syllable_for_phoneme(self, syllables: list, phoneme_index: int) -> int:
        """
        Find which syllable contains the phoneme at the given index.

        Args:
            syllables: List of syllables (each syllable is a list of phonemes)
            phoneme_index: Index into the flattened phoneme list

        Returns:
            Syllable index (0-based), or None if not found
        """
        current_pos = 0
        for syl_idx, syllable in enumerate(syllables):
            syllable_length = len(syllable)
            if current_pos <= phoneme_index < current_pos + syllable_length:
                return syl_idx
            current_pos += syllable_length
        return None

    def _format_syllables_with_stress(self, syllables: list, stressed_syllable_index: int = None) -> str:
        """
        Format syllables with stress marking on the stressed syllable.

        Args:
            syllables: List of syllables (each syllable is a list of phonemes)
            stressed_syllable_index: Index of the stressed syllable (0-based), or None for no stress

        Returns:
            Hyphenated string with stressed syllable in **BOLD CAPS** (e.g., "mal-**KHŪTH**-khā")
        """
        syllable_strings = []
        for idx, syl in enumerate(syllables):
            syl_text = ''.join(syl)
            if idx == stressed_syllable_index:
                # Mark stressed syllable with **BOLD CAPS**
                syl_text = f"**{syl_text.upper()}**"
            syllable_strings.append(syl_text)
        return '-'.join(syllable_strings)

    def _format_syllables_with_multiple_stresses(self, syllables: list, stressed_indices: list = None) -> str:
        """
        Format syllables with stress marking on MULTIPLE stressed syllables.
        Used for maqqef compounds where each component has its own stress.

        Args:
            syllables: List of syllables (each syllable is a list of phonemes)
            stressed_indices: List of stressed syllable indices (0-based), or None/empty for no stress

        Returns:
            Hyphenated string with stressed syllables in **BOLD CAPS** (e.g., "lə-**KHOL**-han-nō-fə-**LIY**-m")
        """
        if stressed_indices is None:
            stressed_indices = []

        syllable_strings = []
        for idx, syl in enumerate(syllables):
            syl_text = ''.join(syl)
            if idx in stressed_indices:
                # Mark stressed syllable with **BOLD CAPS**
                syl_text = f"**{syl_text.upper()}**"
            syllable_strings.append(syl_text)
        return '-'.join(syllable_strings)


if __name__ == '__main__':
    # Example usage for direct testing
    analyst = PhoneticAnalyst()
    psalm_145_1 = "תְּהִלָּה לְדָוִד אֲרוֹמִמְךָ אֱלוֹהַי הַמֶּלֶךְ וַאֲבָרְכָה שִׁמְךָ לְעוֹlָם וָעֶד"
    transcription = analyst.transcribe_verse(psalm_145_1)
    import json
    print(json.dumps(transcription, indent=2, ensure_ascii=False))
