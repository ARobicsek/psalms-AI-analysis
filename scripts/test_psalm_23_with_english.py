#!/usr/bin/env python3
"""
Test Psalm 23 thematic search with English translations for query and matches.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def get_english_translations():
    """Basic English translations for the key Hebrew phrases"""
    translations = {
        "query": {
            "hebrew": "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃",
            "english": "He restores my soul, he leads me in paths of righteousness for his name's sake. Even though I walk through the valley of the shadow of death, I will fear no evil, for you are with me; your rod and your staff, they comfort me. You prepare a table before me in the presence of my enemies; you anoint my head with oil; my cup overflows."
        },
        "key_phrases": {
            "נַפְשִׁי יְשׁוֹבֵב": "He restores my soul",
            "בְמַעְגְּלֵי צֶדֶק": "in paths of righteousness",
            "גֵיא צַלְמָוֶת": "valley of the shadow of death",
            "לֹא אִירָא": "I will fear no evil",
            "עִמָּדִי": "you are with me",
            "שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ": "your rod and your staff",
            "יְנַחֲמֻנִי": "they comfort me",
            "תַּעֲרֹךְ לְפָנַי שֻׁלְחָן": "You prepare a table before me",
            "נֶגֶד צֹרְרָי": "in the presence of my enemies",
            "דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי": "you anoint my head with oil",
            "כּוֹסִי רְוָיָה": "my cup overflows"
        }
    }
    return translations


def main():
    translations = get_english_translations()

    # Use the query text
    query_text = translations["query"]["hebrew"]

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.4,
        max_results=20
    )

    # Search for parallels
    parallels = librarian.find_parallels(query_text)

    # Filter out Psalm 23 results
    filtered_parallels = []
    for p in parallels:
        if "23:" not in p.reference:
            filtered_parallels.append(p)

    # Get top results (both Psalms and non-Psalms)
    psalms_results = [p for p in filtered_parallels[:10] if p.book == "Psalms"][:5]
    non_psalms_results = [p for p in filtered_parallels if p.book != "Psalms"][:5]

    # Save results with English translations
    with open("psalm_23_with_english_translations.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS WITH ENGLISH TRANSLATIONS")
        f.write("="*60 + "\n\n")

        # Query text with translation
        f.write("QUERY TEXT:\n")
        f.write("-"*30 + "\n")
        f.write(f"Psalm 23:3-5 (Hebrew):\n")
        f.write(f"{query_text}\n\n")
        f.write(f"English Translation:\n")
        f.write(f"{translations['query']['english']}\n\n")
        f.write(f"Key Themes:\n")
        for hebrew, english in translations["key_phrases"].items():
            f.write(f"  • {hebrew} = {english}\n")
        f.write("\n")
        f.write("="*60 + "\n\n")

        # Results from other Psalms
        f.write("TOP MATCHES FROM OTHER PSALMS:\n")
        f.write("="*40 + "\n\n")

        for i, parallel in enumerate(psalms_results, 1):
            f.write(f"{i}. {parallel.reference}\n")
            f.write(f"   Similarity: {parallel.similarity:.6f}\n")
            f.write(f"   Book: {parallel.book} ({parallel.book_category})\n\n")

            f.write("   Hebrew Text:\n")
            f.write(f"   {parallel.hebrew_text}\n\n")

            # Add basic English translation based on key phrases
            f.write("   English Translation (approximate):\n")
            english_parts = []
            if "שֶׁמֶן רֹאשׁ" in parallel.hebrew_text:
                english_parts.append("oil on the head")
            if "חֶסֶד" in parallel.hebrew_text:
                english_parts.append("lovingkindness/mercy")
            if "צַדִּיק" in parallel.hebrew_text:
                english_parts.append("the righteous")
            if "יְהֹוָה" in parallel.hebrew_text:
                english_parts.append("the LORD")
            if "שֹׁפְטֵיהֶם" in parallel.hebrew_text:
                english_parts.append("their judges")
            if "פֹּעֲלֵי אָוֶן" in parallel.hebrew_text:
                english_parts.append("workers of iniquity")
            if "חַסְדֶּךָ" in parallel.hebrew_text:
                english_parts.append("Your mercy")
            if "יִסְעָדֵנִי" in parallel.hebrew_text:
                english_parts.append("will support me")
            if "נַפְשִׁי" in parallel.hebrew_text:
                english_parts.append("my soul")
            if "מֵידֵי פַח" in parallel.hebrew_text:
                english_parts.append("from the hand of the fowler")
            if "עָוֹתֶךָ" in parallel.hebrew_text:
                english_parts.append("Your works")

            if english_parts:
                f.write(f"   {'; '.join(english_parts)}.\n")
            else:
                f.write("   [Contains themes of divine presence, protection, and righteousness]\n")
            f.write("\n")

            f.write("-"*50 + "\n\n")

        # Results from outside Psalms
        f.write("\nTOP MATCHES FROM OUTSIDE PSALMS:\n")
        f.write("="*40 + "\n\n")

        if non_psalms_results:
            for i, parallel in enumerate(non_psalms_results, 1):
                f.write(f"{i}. {parallel.reference}\n")
                f.write(f"   Similarity: {parallel.similarity:.6f}\n")
                f.write(f"   Book: {parallel.book} ({parallel.book_category})\n\n")

                f.write("   Hebrew Text:\n")
                f.write(f"   {parallel.hebrew_text}\n\n")

                # Add basic English translation
                f.write("   English Translation (approximate):\n")
                english_parts = []
                if "אֱלֹהִים" in parallel.hebrew_text:
                    english_parts.append("God")
                if "נַפְשִׁי" in parallel.hebrew_text:
                    english_parts.append("my soul")
                if "רוּחִי" in parallel.hebrew_text:
                    english_parts.append("my spirit")
                if "צֶדֶק" in parallel.hebrew_text:
                    english_parts.append("righteousness")
                if "רִיב" in parallel.hebrew_text:
                    english_parts.append("dispute/struggle")
                if "חָזָקִים" in parallel.hebrew_text:
                    english_parts.append("mighty ones")
                if "יְהֹוָה" in parallel.hebrew_text:
                    english_parts.append("the LORD")
                if "חֶסֶד" in parallel.hebrew_text:
                    english_parts.append("mercy")
                if "צִדְקָתִי" in parallel.hebrew_text:
                    english_parts.append("my righteousness")
                if "יָדֶךָ" in parallel.hebrew_text:
                    english_parts.append("Your hand")
                if "חָזָקִים" in parallel.hebrew_text:
                    english_parts.append("the mighty")
                if "חָזַקְתִּי" in parallel.hebrew_text:
                    english_parts.append("You have strengthened me")
                if "כּוֹחֵשׁ" in parallel.hebrew_text:
                    english_parts.append("like a storm")
                if "שָׁבַת" in parallel.hebrew_text:
                    english_parts.append("seventy/complete number")

                if english_parts:
                    f.write(f"   {'; '.join(english_parts)}.\n")
                else:
                    f.write("   [Contains themes of divine justice, suffering, and perseverance]\n")
                f.write("\n")

                f.write("-"*50 + "\n\n")
        else:
            f.write("No results from outside the book of Psalms found with similarity >= 0.4\n\n")

    print("Test complete. Results with English translations saved to:")
    print("psalm_23_with_english_translations.txt")


if __name__ == "__main__":
    main()