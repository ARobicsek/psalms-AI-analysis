"""
This module defines the PhoneticAnalyst agent, which is responsible for
transcribing Hebrew text into a detailed phonetic and syllabic structure
based on reconstructed Biblical Hebrew phonology.
"""

import gzip
import json
import os
import re

import unicodedata2 as unicodedata

class PhoneticAnalyst:
    """
    An agent that analyzes Hebrew text and produces a phonetic transcription.
    """

    # ------------------------------------------------------------------
    # Cantillation marks and word stress
    #
    # A te'amim glyph marks the stressed syllable only if the accent is
    # *impositive*. Prepositive accents are written on the first letter of the
    # word and postpositive accents on the last, no matter which syllable is
    # stressed, so for those the glyph position is not evidence. Two marks are
    # additionally ambiguous:
    #
    #   * U+05BD is both silluq (the stress accent of the last word of a verse)
    #     and meteg (a secondary-stress tick that lands anywhere). Anywhere but
    #     the verse-final word it is a meteg and must not be read as the stress.
    #   * U+0598 is named "ZARQA" in Unicode but does double duty. Paired with
    #     U+05AE it is the prose zarqa and does mark the stress; paired with
    #     mahpakh or merkha it is the poetic tsinnorit, a helper tick sitting on
    #     an earlier letter that marks nothing. Ranking it below the reliable
    #     accents resolves both cases.
    #
    # Percentages are measured over the ~192K accented words of
    # database/tanakh.db -- the rate at which a mark's letter is the stressed
    # letter, with ground truth taken from other occurrences of the same pointed
    # form carrying a single unambiguous accent.
    # ------------------------------------------------------------------
    _METEG = 'ֽ'  # U+05BD
    _TSINNORIT = '֘'  # U+0598
    _SOF_PASUQ = '׃'  # U+05C3

    # Glyph sits on the stressed syllable.
    _POSITION_RELIABLE = frozenset([
        '֑',  # Etnahta (U+0591)             99.9%
        '֓',  # Shalshelet (U+0593)          100.0%
        '֔',  # Zaqef Qaton (U+0594)         99.8%
        '֕',  # Zaqef Gadol (U+0595)         99.7%
        '֖',  # Tifcha (U+0596)              99.8%
        '֗',  # Revia (U+0597)               99.7%
        '֚',  # Yetiv (U+059A)               99.4%
        '֛',  # Tevir (U+059B)               100.0%
        '֜',  # Geresh (U+059C)              99.9%
        '֞',  # Gershayim (U+059E)           99.5%
        '֟',  # Qarney Para (U+059F)         100.0%
        '֠',  # Telisha Gedola (U+05A0)      97.2%
        '֡',  # Pazer (U+05A1)               99.6%
        '֢',  # Atnah Hafukh (U+05A2)        98.2%
        '֣',  # Munach (U+05A3)              97.3%
        '֤',  # Mahpakh (U+05A4)             99.0%
        '֥',  # Mercha (U+05A5)              99.0%
        '֦',  # Mercha Kefula (U+05A6)       100.0%
        '֧',  # Darga (U+05A7)               99.6%
        '֨',  # Qadma (U+05A8)               97.1%
        '֪',  # Yerach ben Yomo (U+05AA)     92.5%
        '֬',  # Iluy (U+05AC)                97.0%
    ])

    # Written on the LAST letter of the word. When the same mark appears twice,
    # the inner copy is the stress (segolta 100.0%, pashta 99.8%, telisha
    # qetana 98.5%); a single occurrence means the stress *is* final, which is
    # why no second copy was needed.
    _POSTPOSITIVE = frozenset([
        '֒',  # Segolta (U+0592)             0.2% single
        '֙',  # Pashta (U+0599)              2.2% single
        '֩',  # Telisha Qetana (U+05A9)      0.3% single
        '֮',  # Zinor (U+05AE)               1.6% single
    ])

    # Written on the FIRST letter of the word, with no doubling convention to
    # recover the stress from -- position here is pure noise.
    _PREPOSITIVE = frozenset([
        '֝',  # Geresh Muqdam (U+059D)       8.8%
        '֫',  # Ole (U+05AB)                 7.0%
        '֭',  # Dehi (U+05AD)                11.2%
    ])

    _ALL_ACCENTS = (_POSITION_RELIABLE | _POSTPOSITIVE | _PREPOSITIVE
                    | frozenset([_METEG, _TSINNORIT]))

    # A vowel letter (mater lectionis) fuses with the preceding vowel into one
    # long vowel rather than adding a consonant and a syllable of its own.
    _YOD_MATER = {'i': 'iy', 'ē': 'ēy', 'e': 'ey'}

    _VOWEL_PHONEMES = (frozenset(['a', 'ā', 'e', 'ē', 'i', 'ī', 'o', 'ō', 'u', 'ū', 'ə'])
                       | frozenset(_YOD_MATER.values()))

    # How much to trust a stressed_syllable_index, keyed by how it was found.
    _STRESS_CONFIDENCE = {'accent': 2, 'doubled': 1, 'tsinnorit': 1, 'lexicon': 1}

    # Letters that never take dagesh forte; a dagesh on these is mappiq
    # (consonantal he) or an oddity, and must not geminate.
    _NEVER_GEMINATE = frozenset('אהחער')

    # Marks dropped when keying the stress lexicon, so that one entry serves a
    # form however it happens to be accented or punctuated in a given verse.
    _KEY_DROP = frozenset(['׃', '׀'])

    # Where dehi, geresh muqdam and ole leave no positional evidence, the stress
    # is looked up here: the same pointed form read off ANOTHER verse where the
    # accent is unambiguous. Built by scripts/build_stress_lexicon.py; the values
    # are LETTER indices, not syllable indices, so the file survives changes to
    # the syllabifier. Absent file -> the default ultima stress, no error.
    _LEXICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'stress_lexicon.json.gz')

    def __init__(self, stress_lexicon=None):
        """
        Initializes the PhoneticAnalyst with mappings based on the reference guide.

        Args:
            stress_lexicon: optional {pointed form: stressed letter index} map.
                Defaults to the bundled lexicon, loaded on first use.
        """
        self._stress_lexicon = stress_lexicon
        self._lexicon_loaded = stress_lexicon is not None
        self.consonant_map = {
            'א': "'", 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'w', 'ז': 'z',
            'ח': 'ḥ', 'ט': 't', 'י': 'y', 'כ': 'k', 'ך': 'kh', 'ל': 'l', 'מ': 'm',
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
        # Unicode characters
        self.dagesh = '\u05BC'
        self.shin_dot = '\u05C1'
        self.sin_dot = '\u05C2'
        self.qamets = '\u05B8'
        self.patah = '\u05B7'
        self.shewa = '\u05B0'
        self.holam = '\u05B9'
        self.holam_haser_vav = '\u05BA'


    def transcribe_verse(self, hebrew_verse: str) -> dict:
        """
        Transcribes a full Hebrew verse into a structured phonetic format.
        Handles ketiv-qere notation: (ketiv) [qere] - only transcribes the qere.
        """
        # Normalize to handle composite characters
        normalized_verse = unicodedata.normalize('NFD', hebrew_verse)

        # Handle ketiv-qere: remove (ketiv) and unwrap [qere]
        # Pattern: (text) [text] -> keep only the bracketed text
        # Remove parenthetical ketiv (what is written but not read)
        normalized_verse = re.sub(r'\([^)]*\)\s*', '', normalized_verse)
        # Unwrap bracketed qere (what is read)
        normalized_verse = re.sub(r'\[([^\]]*)\]', r'\1', normalized_verse)
        # Drop editorial section markers -- {פ} petuhah, {ס} setumah, {ש} shirah.
        # These are not words; left in, the peh transcribed as a phantom "f".
        normalized_verse = re.sub(r'\{[^}]*\}', '', normalized_verse)

        # The sof pasuq (׃) is deliberately NOT stripped: it is how a word is
        # recognised as verse-final, which is what tells silluq from meteg.
        words = [self._transcribe_word(w) for w in normalized_verse.split()]

        analysis = {
            "original_text": hebrew_verse,
            # Punctuation-only tokens (paseq ׀, a stray sof pasuq) yield no
            # phonemes; keeping them injected empty strings into the output.
            "words": [w for w in words if w["phonemes"]]
        }
        return analysis

    def _transcribe_word(self, hebrew_word: str) -> dict:
        """
        Transcribes a single Hebrew word.

        Stress comes from the cantillation via _stress_letter(), which names a
        LETTER; the stressed syllable is then the one holding that letter's last
        phoneme. Resolving through the letter (rather than counting phonemes as
        they are emitted) keeps the mapping right when a letter contributes an
        unexpected number of phonemes -- a geminated consonant contributes two,
        a mater lectionis one, a silent shewa none.

        Where the accents give no position (a prepositive accent, or none at
        all) the form is looked up in the stress lexicon, and only failing that
        does the default ultima stress apply. `stress_source` in the result says
        which of the three answered, so an inferred stress is never mistaken for
        one the Masoretes wrote down.

        Maqqef compounds (word1-word2) are handled separately: they form one
        accent domain, so only the last component carries the stress.
        """
        if '\u05be' in hebrew_word:
            return self._transcribe_maqqef_compound(hebrew_word)

        phonemes, transcription, phoneme_letter, letter_accents, furtive_letter = \
            self._scan_word(hebrew_word)

        syllables = self._syllabify(phonemes)
        syllable_string = self._format_syllables(syllables)

        # --- Stress ------------------------------------------------------
        stress_letter, stress_source = self._stress_letter(letter_accents, hebrew_word)
        if stress_letter is None:
            # No positional evidence in this verse's accents. Before guessing,
            # look the form up where the Masoretes did accent it unambiguously.
            from_lexicon = self._lexicon_stress_letter(hebrew_word)
            if from_lexicon is not None:
                stress_letter, stress_source = from_lexicon, 'lexicon'

        stressed_syllable_index = None
        if stress_letter is not None:
            stressed_syllable_index = self._find_syllable_for_letter(
                syllables, phoneme_letter, stress_letter)
            if stressed_syllable_index is None:
                stress_source = 'ultima-default'
        if stressed_syllable_index is None and syllables:
            # No usable position in the cantillation: fall back to the default
            # Hebrew ultima stress. stress_source records that it was inferred.
            stressed_syllable_index = len(syllables) - 1
            # A furtive patah is never stressed, so the default has to step back
            # over it: ruah is RU-ah, never ru-AH.
            if furtive_letter is not None and stressed_syllable_index > 0:
                furtive_syllable = self._find_syllable_for_letter(
                    syllables, phoneme_letter, furtive_letter)
                if furtive_syllable == stressed_syllable_index:
                    stressed_syllable_index -= 1

        stressed_syllable_string = self._format_syllables_with_stress(
            syllables, stressed_syllable_index)

        return {
            "word": unicodedata.normalize('NFC', hebrew_word),
            "transcription": "".join(transcription),
            "syllables": syllables,  # List of syllables (each is list of phonemes)
            "syllable_transcription": syllable_string,  # e.g. "te-hil-lah"
            "syllable_transcription_stressed": stressed_syllable_string,  # **BOLD CAPS**
            "stressed_syllable_index": stressed_syllable_index,  # 0-indexed
            # 2 = read straight off a position-reliable accent; 1 = recovered
            # from a doubled accent, a tsinnorit, or the lexicon; 0 = inferred by
            # the default ultima stress. stress_source says which.
            "stress_level": self._STRESS_CONFIDENCE.get(stress_source, 0),
            "stress_source": stress_source,
            "phonemes": phonemes
        }

    def _scan_word(self, hebrew_word: str):
        """
        Walk a word letter by letter and produce its phonemes.

        Returns (phonemes, transcription, phoneme_letter, letter_accents,
        furtive_letter), where phoneme_letter[n] is the index in the word of the
        letter that produced phonemes[n] -- the link the stress logic needs, and
        the reason this is separated from the packaging in _transcribe_word.
        """
        phonemes = []
        transcription = []
        phoneme_letter = []   # index in `chars` of the letter that produced each phoneme
        letter_accents = []   # (index in `chars`, mark) for every accent in the word
        furtive_letter = None  # letter carrying a furtive patah, if any

        def emit(sound, letter):
            phonemes.append(sound)
            transcription.append(sound)
            phoneme_letter.append(letter)

        chars = list(hebrew_word)
        i = 0
        while i < len(chars):
            char = chars[i]
            if char not in self.consonant_map:
                i += 1
                continue

            # Collect this letter's points and accents
            j = i + 1
            modifiers = []
            while j < len(chars) and unicodedata.category(chars[j]) == 'Mn':
                modifiers.append(chars[j])
                if chars[j] in self._ALL_ACCENTS:
                    letter_accents.append((i, chars[j]))
                j += 1

            has_dagesh = self.dagesh in modifiers
            own_vowel = next((m for m in modifiers if m in self.vowel_map), None)

            # --- Vav as a vowel letter --------------------------------------
            if char == '\u05d5':
                if has_dagesh and own_vowel is None:
                    emit('\u016b', i)          # shureq
                    i = j
                    continue
                if not has_dagesh and (self.holam in modifiers
                                       or self.holam_haser_vav in modifiers):
                    emit('\u014d', i)          # holam male
                    i = j
                    continue
                # A vav carrying its own vowel is a consonantal waw, and with a
                # dagesh a doubled one: without this guard the dagesh read as a
                # shureq and Havvah came out as ha-u instead of haw-wah.

            # --- Yod as a vowel letter -------------------------------------
            # hiriq/tsere/segol plus a bare yod is one long vowel, not a vowel
            # followed by a consonant: Elohim is 'e-lo-hiym, never 'e-lo-hiy-m,
            # which added a phantom final syllable and pulled the stress back.
            if (char == '\u05d9' and own_vowel is None and not has_dagesh
                    and phonemes and phonemes[-1] in self._YOD_MATER):
                merged = self._YOD_MATER[phonemes[-1]]
                phonemes[-1] = merged
                transcription[-1] = merged
                i = j
                continue

            # --- Consonant -------------------------------------------------
            consonant_sound = self.consonant_map[char]
            if char == '\u05e9' and self.sin_dot in modifiers:
                consonant_sound = 's'
            if char in self.begadkefat_soft and not has_dagesh:
                consonant_sound = self.begadkefat_soft[char]

            is_geminated = self._is_dagesh_forte(i, chars)
            vowel_sound = self.vowel_map[own_vowel] if own_vowel else ''

            # Furtive patah: under a word-final het, ayin or he-with-mappiq the
            # patah is pronounced BEFORE the consonant -- ruah is ru-ah.
            is_furtive_patach = (
                vowel_sound == 'a'
                and char in ('\u05d7', '\u05e2', '\u05d4')
                and not any(c in self.consonant_map for c in chars[j:])
            )

            if is_furtive_patach:
                furtive_letter = i
                emit(vowel_sound, i)
                emit(consonant_sound, i)
            else:
                emit(consonant_sound, i)
                if is_geminated:
                    emit(consonant_sound, i)
                if vowel_sound and not (vowel_sound == '\u0259'
                                        and not self._is_vocal_shewa(i, chars)):
                    emit(vowel_sound, i)

            i = j

        return phonemes, transcription, phoneme_letter, letter_accents, furtive_letter

    def _stress_letter(self, letter_accents, hebrew_word):
        """
        Decide which LETTER of a word carries the stress, from its accents.

        Returns (index into the word's characters, source tag). A None index
        means the cantillation offers no usable position and the caller should
        fall back to the default ultima stress.
        """
        if not letter_accents:
            return None, 'ultima-default'

        # U+05BD is silluq on the verse-final word and meteg everywhere else.
        # Meteg marks a secondary stress and sits away from the main one in 99%
        # of cases, so reading it as the accent stole the stress from the real
        # one in 4,313 words of the Tanakh.
        metegs = [li for li, m in letter_accents if m == self._METEG]
        real = [(li, m) for li, m in letter_accents if m != self._METEG]
        silluq = metegs[-1] if (self._SOF_PASUQ in hebrew_word and metegs) else None

        # A mark repeated inside one word is the doubling convention: the copy
        # away from the word edge is the one sitting on the stress.
        repeated = {}
        for li, mark in real:
            repeated.setdefault(mark, []).append(li)
        for mark, positions in repeated.items():
            if len(positions) > 1:
                inner = min(positions) if mark in self._POSTPOSITIVE else max(positions)
                return inner, 'doubled'

        reliable = [li for li, m in real if m in self._POSITION_RELIABLE]
        if silluq is not None:
            reliable.append(silluq)
        if reliable:
            return max(reliable), 'accent'

        # The tsinnorit ranks below the reliable accents. Reached only when
        # nothing reliable is present -- i.e. its partner is a zinor and the
        # pair is the prose zarqa, where U+0598 does mark the stress (99.2%).
        tsinnorit = [li for li, m in real if m == self._TSINNORIT]
        if tsinnorit:
            return max(tsinnorit), 'tsinnorit'

        # A single postpositive accent means the stress IS final: that is
        # precisely why the scribe did not need to write a second copy.
        if any(m in self._POSTPOSITIVE for _, m in real):
            return None, 'ultima-by-convention'

        # Prepositive only (dehi, geresh muqdam, ole) -- position is noise.
        return None, 'ultima-default'

    @classmethod
    def lexicon_key(cls, hebrew_word: str) -> str:
        """
        Canonical key for the stress lexicon: the pointed form with accents and
        punctuation removed, so one entry covers every accentuation of a form.
        Used by both the lookup and scripts/build_stress_lexicon.py.
        """
        return ''.join(c for c in unicodedata.normalize('NFD', hebrew_word)
                       if c not in cls._ALL_ACCENTS and c not in cls._KEY_DROP)

    def _load_stress_lexicon(self) -> dict:
        """Read the bundled lexicon; an absent or unreadable file is not fatal."""
        try:
            with gzip.open(self._LEXICON_FILE, 'rt', encoding='utf-8') as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _lexicon_stress_letter(self, hebrew_word: str):
        """
        Character index of the stressed letter per the lexicon, or None.

        Consulted only when the cantillation gives no usable position, so it can
        never override an accent that is actually there.
        """
        if not self._lexicon_loaded:
            self._stress_lexicon = self._load_stress_lexicon()
            self._lexicon_loaded = True
        letter_index = self._stress_lexicon.get(self.lexicon_key(hebrew_word))
        if letter_index is None:
            return None
        return self._char_index_of_letter(list(hebrew_word), letter_index)

    def _char_index_of_letter(self, chars: list, letter_index: int):
        """Position in `chars` of the nth letter, counting consonants only."""
        n = -1
        for pos, ch in enumerate(chars):
            if ch in self.consonant_map:
                n += 1
                if n == letter_index:
                    return pos
        return None

    def _find_syllable_for_letter(self, syllables, phoneme_letter, letter_index):
        """
        Which syllable carries the accent written on `letter_index`.

        Resolved through the letter's LAST phoneme, which matters for a
        geminated consonant: its first copy closes the preceding syllable while
        the second opens the stressed one, so the accent on the bet of Rabbim
        belongs to rab-BIYM, not to RAB.
        """
        positions = [n for n, li in enumerate(phoneme_letter) if li == letter_index]
        if not positions:
            return None
        return self._find_syllable_for_phoneme(syllables, positions[-1])

    def _previous_consonant(self, index, chars):
        """Index of the nearest consonant before `index`, or None."""
        for k in range(index - 1, -1, -1):
            if chars[k] in self.consonant_map:
                return k
        return None

    def _vowel_of(self, consonant_index, limit, chars):
        """The vowel point belonging to the consonant at `consonant_index`."""
        for k in range(consonant_index + 1, min(limit, len(chars))):
            if chars[k] in self.vowel_map:
                return chars[k]
        return None

    def _is_dagesh_forte(self, index, chars):
        """
        Is the dagesh on the consonant at `index` forte (doubling the letter)
        rather than lene (merely hardening a begadkefat)?

        Dagesh lene occurs only where the consonant is not preceded by a vowel
        sound: word-initially, or after a syllable closed by a silent shewa
        (mishpat is mish-pat, not mish-ppat). Anywhere else a dagesh doubles.
        """
        char = chars[index]
        if char in self._NEVER_GEMINATE:
            # A dagesh on these is mappiq (consonantal he) or a scribal oddity.
            # Doubling it invented a syllable: Halleluyah came out hal-lu-yah-h.
            return False

        has_dagesh = False
        k = index + 1
        while k < len(chars) and unicodedata.category(chars[k]) == 'Mn':
            if chars[k] == self.dagesh:
                has_dagesh = True
                break
            k += 1
        if not has_dagesh:
            return False

        prev = self._previous_consonant(index, chars)
        if prev is None:
            # Word-initial: nothing for a geminate to close, whatever the letter.
            # Some conjunctive dageshim do land here (זֹּאת), and doubling them
            # produced onsets like "zzo'-th".
            return False
        if char not in self.begadkefat_soft:
            return True   # a dagesh on a non-begadkefat can only be forte

        prev_vowel = self._vowel_of(prev, index, chars)
        if prev_vowel is None:
            return False  # nothing voiced before it -> lene
        if prev_vowel == self.shewa:
            return self._is_vocal_shewa(prev, chars)
        return True

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
        last_component_stress_source = 'ultima-default'

        # The LAST NON-EMPTY component is the one that carries the stress. Using
        # the raw index instead left a compound ending in a stray maqqef with no
        # stress at all.
        populated = [n for n, c in enumerate(components) if c]

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
            if i == populated[-1] and result['stressed_syllable_index'] is not None:
                last_component_stress_index = syllable_offset + result['stressed_syllable_index']
                last_component_stress_level = result['stress_level']
                last_component_stress_source = result['stress_source']

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
            "stress_source": last_component_stress_source,
            "phonemes": [p for syl in all_syllables for p in syl]  # Flatten
        }

    def _is_vocal_shewa(self, index, chars):
        """
        Is the shewa on the consonant at `index` vocal (pronounced as a reduced
        vowel) or silent (merely closing the preceding syllable)?
        """
        # 1. A word-final shewa is always silent. Voicing it invented a syllable
        #    and dragged the stress off the last one: lehithhallekh came out as
        #    le-hith-hal-le-KHE instead of le-hith-hal-LEKH.
        if not any(c in self.consonant_map for c in chars[index + 1:]):
            return False

        prev_consonant_idx = self._previous_consonant(index, chars)
        # 2. Shewa under the first letter of a word is vocal.
        if prev_consonant_idx is None:
            return True

        # 3. Shewa under a consonant doubled by dagesh forte is vocal
        #    (dabberu is dab-be-ru). Tested BEFORE the short-vowel rule, which
        #    would otherwise short-circuit and call it silent -- the original
        #    ordering made this branch unreachable.
        if self._is_dagesh_forte(index, chars):
            return True

        prev_vowel = self._vowel_of(prev_consonant_idx, index, chars)
        # 4. Shewa after a consonant with no vowel (start of a cluster) is vocal.
        if prev_vowel is None:
            return True

        # 5. The second of two consecutive shewas is vocal: weyismehu is
        #    we-yis-me-hu, not we-yis-MHU.
        if prev_vowel == self.shewa:
            return True

        # 6. Shewa after a short vowel is silent (the syllable is closed).
        #    Short vowels are Patah, Segol, Hiriq, Qubuts, Qamets Qatan.
        short_vowels = ['\u05B7', '\u05B6', '\u05B4', '\u05BB', '\u05C7']
        if prev_vowel in short_vowels:
            return False

        # 7. Shewa after a long vowel is vocal (the syllable is open).
        #    Long vowels are Qamets, Tsere, Holam.
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
        
        # Define what counts as a vowel (includes the mater lectionis digraphs,
        # which are single long vowels and must not be split)
        vowels = self._VOWEL_PHONEMES
        
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
        
        # Any leftover is a run of consonants with no vowel of its own -- a
        # word-final cluster, as in zo'th or 'elayw. It belongs to the preceding
        # syllable; appended as a syllable it became a phantom that could not be
        # pronounced and that the ultima default would then stress ("ro'-SH").
        if current_syllable:
            if syllables and not any(p in vowels for p in current_syllable):
                syllables[-1].extend(current_syllable)
            else:
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
    # Example usage for direct testing. Accented text is required: without the
    # te'amim every word falls back to the default ultima stress.
    import sys

    sys.stdout.reconfigure(encoding='utf-8')

    analyst = PhoneticAnalyst()
    samples = {
        # Ps 145:1 -- gemination, silent vs vocal shewa, final kaf
        'Ps 145:1': "תְּהִלָּ֗ה לְדָ֫וִ֥ד אֲרוֹמִמְךָ֣ אֱלוֹהַ֣י הַמֶּ֑לֶךְ "
                    "וַאֲבָרְכָ֥ה שִׁמְךָ֗ לְעוֹלָ֥ם וָעֶֽד׃",
        # Ps 70:4-5 -- dehi (no positional evidence) and the tsinnorit/mahpakh pair
        'Ps 70:4': "יָ֭שׁוּבוּ עַל־עֵ֣קֶב בׇּשְׁתָּ֑ם הָ֝אֹמְרִ֗ים הֶ֘אָ֥ח ׀ הֶאָֽח׃",
        'Ps 70:5': "יָ֘שִׂ֤ישׂוּ וְיִשְׂמְח֨וּ ׀ בְּךָ֗ כׇּֽל־מְבַ֫קְשֶׁ֥יךָ "
                   "וְיֹאמְר֣וּ תָ֭מִיד יִגְדַּ֣ל אֱלֹהִ֑ים אֹ֝הֲבֵ֗י יְשׁוּעָתֶֽךָ׃",
    }
    for ref, verse in samples.items():
        analysis = analyst.transcribe_verse(verse)
        print(f'\n{ref}')
        for word in analysis['words']:
            print(f"  {word['word']:22s} {word['syllable_transcription_stressed']:32s}"
                  f" [{word['stress_source']}]")
    print('\nfull structure for Ps 70:4:')
    print(json.dumps(analyst.transcribe_verse(samples['Ps 70:4']), indent=2,
                     ensure_ascii=False))
