"""
Test the fixed _extract_context method to ensure it now includes the matched phrase.
"""
import sys
sys.path.append('.')

from src.liturgy.liturgy_indexer import LiturgyIndexer

# Initialize indexer
indexer = LiturgyIndexer(verbose=False)

# Test case 1: From Psalm 1 - "בַּעֲצַת רְשָׁעִים"
test_phrase = "בַּעֲצַת רְשָׁעִים"

# This is the prayer text that contains it (abbreviated for testing)
liturgy_text = """
יְהִי רָצוֹן מִלְּפָנֶיךָ יְהֹוָה אֱלֹהֵינוּ וֵאלֹהֵי אֲבוֹתֵינוּ, שֶׁבִּזְכוּת הַקָּפָה חֲמִישִׁית הָרוֹמֶזֶת לְמִדַּת הַהוֹד.
וּתְזַכֵּנוּ לְכַבֵּד הַתּוֹרָה וְלוֹמְדֶיהָ, וּלְהַחֲזִיק וּלְאַמֵּץ בִּרְכַּיִם כּוֹשְׁלוֹת, הַנֵּי בִּרְכֵּי דְרַבָּנָן דְּשַׁלְהֵי,
וּתְזַכֵּנוּ שֶׁלֹּא נֵלֵךְ בַּעֲצַת רְשָׁעִים, וְלֹא נִהְיֶה מֵהוֹלְכֵי רָכִיל, וּלְמַעַן זְכוּת אַהֲרֹן קְדוֹשׁ יְהֹוָה הֶחָתוּם בְּמִדַּת הוֹד לְטוֹבָה.
"""

# Extract context using the fixed method
context = indexer._extract_context(liturgy_text, test_phrase, context_words=10)

# Write results to file
with open('output/context_fix_test.txt', 'w', encoding='utf-8') as f:
    f.write("Test: Context Extraction Fix\n")
    f.write("=" * 60 + "\n")
    f.write(f"Psalm phrase: {test_phrase}\n")
    f.write(f"\nExtracted context ({len(context)} chars):\n")
    f.write(context + "\n")
    f.write("\n")

    # Check if the phrase is in the context
    if test_phrase in context:
        f.write("✅ SUCCESS: Matched phrase IS in the extracted context!\n")
    else:
        # Also check normalized version
        normalized_phrase = indexer._full_normalize(test_phrase)
        normalized_context = indexer._full_normalize(context)
        if normalized_phrase in normalized_context:
            f.write("✅ SUCCESS: Matched phrase found in normalized context!\n")
        else:
            f.write("❌ FAILURE: Matched phrase NOT in context!\n")
            f.write(f"\nNormalized phrase: {normalized_phrase}\n")
            f.write(f"Normalized context: {normalized_context}\n")

print("Test results written to output/context_fix_test.txt")
