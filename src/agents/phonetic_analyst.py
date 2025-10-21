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
            'ַ': 'a', 'ָ': 'ā', 'ֵ': 'ē', 'ֶ': 'e', 'ִ': 'i', 'ֹ': 'ō', 'ֺ': 'ō',
            'ֻ': 'u', 'ּ': 'u', 'ְ': 'ə', 'ֲ': 'a', 'ֱ': 'e', 'ֳ': 'o'
        }
        self.begadkefat_soft = {
            'ב': 'v', 'ג': 'gh', 'ד': 'dh', 'כ': 'kh', 'פ': 'f', 'ת': 'th'
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
        """
        # Normalize to handle composite characters
        normalized_verse = unicodedata.normalize('NFD', hebrew_verse)
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
        """
        phonemes = []
        transcription = []
        
        chars = list(hebrew_word)
        i = 0
        while i < len(chars):
            char = chars[i]
            
            # --- Consonant Logic ---
            if char in self.consonant_map:
                # Look ahead for dagesh, shin/sin dots, and vowels
                j = i + 1
                modifiers = []
                while j < len(chars) and unicodedata.category(chars[j]) == 'Mn':
                    modifiers.append(chars[j])
                    j += 1

                # === NEW: Check if vav is serving as mater lectionis ===
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
                
                # === END NEW CODE ===

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
                # A proper implementation needs to check if it's post-vocalic
                if is_begadkefat and not has_dagesh:
                    consonant_sound = self.begadkefat_soft[char]

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

        return {
            "word": unicodedata.normalize('NFC', hebrew_word),
            "transcription": "".join(transcription),
            "syllables": [], # Placeholder for Step 3
            "phonemes": phonemes
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


if __name__ == '__main__':
    # Example usage for direct testing
    analyst = PhoneticAnalyst()
    psalm_145_1 = "תְּהִלָּה לְדָוִד אֲרוֹמִמְךָ אֱלוֹהַי הַמֶּלֶךְ וַאֲבָרְכָה שִׁמְךָ לְעוֹלָם וָעֶד"
    transcription = analyst.transcribe_verse(psalm_145_1)
    import json
    print(json.dumps(transcription, indent=2, ensure_ascii=False))
