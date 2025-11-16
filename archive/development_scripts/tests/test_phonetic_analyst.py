"""
Tests for the PhoneticAnalyst agent.
"""
import unittest
import json
from src.agents.phonetic_analyst import PhoneticAnalyst

# It's often useful to have a central place for test data
PSALM_145_HEBREW = {
    1: "תְּהִלָּה לְדָוִד אֲרוֹמִמְךָ אֱלוֹהַי הַמֶּלֶךְ וַאֲבָרְכָה שִׁמְךָ לְעוֹלָם וָעֶד",
    2: "בְּכׇל־יוֹם אֲבָרְכֶךָּ וַאֲהַלְלָה שִׁמְךָ לְעוֹלָם וָעֶד",
    3: "גָּדוֹל יְהוָה וּמְהֻלָּל מְאֹד וְלִגְדֻלָּתוֹ אֵין חֵקֶר",
    4: "דּוֹר לְדוֹר יְשַׁבַּח מַעֲשֶׂיךָ וּגְבוּרֹתֶיךָ יַגִּידוּ",
    5: "הֲדַר כְּבוֹד הוֹדֶךָ וְדִבְרֵי נִפְלְאֹתֶיךָ אָשִׂיחָה",
    6: "וְעֵז וּז נוֹרְאֹתֶיךָ יֹאמֵרוּ וּגְדֻלָּתְךָ אֲסַפְּרֶנָּה",
    7: "זֵכֶר רַב־טוּבְךָ יַבִּיעוּ וְצִדְקָתְךָ יְרַנֵּנוּ",
    8: "חַנּוּן וְרַחוּם יְהוָה אֶרֶךְ אַפַּיִם וּגְדׇל־חָסֶד",
    9: "טוֹב־יְהוָה לַכֹּל וְרַחֲמָיו עַל־כׇּל־מַעֲשָׂיו",
    10: "יוֹדוּךָ יְהוָה כׇּל־מַעֲשֶׂיךָ וַחֲסִידֶיךָ יְבָרְכוּכָה",
    11: "כְּבוֹד מַלְכוּתְךָ יֹאמֵרוּ וּגְבוּרָתְךָ יְדַבֵּרוּ",
    12: "לְהוֹדִיעַ לִבְנֵי הָאָדָם גְּבוּרֹתָיו וּכְבוֹד הֲדַר מַלְכוּתוֹ",
    13: "מַלְכוּתְךָ מַלְכוּת כׇּל־עֹלָמִים וּמֶמְשַׁלְתְּךָ בְּכׇל־דּוֹר וָדֹר",
    14: "סוֹמֵךְ יְהוָה לְכׇל־הַנֹּפְלִים וְזוֹקֵף לְכׇל־הַכְּפוּפִים",
    15: "עֵינֵי־כֹל אֵלֶיךָ יְשַׂבֵּרוּ וְאַתָּה נוֹתֵן־לָהֶם אֶת־אׇכְלָם בְּעִתּוֹ",
    16: "פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן",
    17: "צַדִּיק יְהוָה בְּכׇל־דְּרָכָיו וְחָסִיד בְּכׇל־מַעֲשָׂיו",
    18: "קָרוֹב יְהוָה לְכׇל־קֹרְאָיו לְכֹל אֲשֶׁר יִקְרָאֻהוּ בֶאֱמֶת",
    19: "רְצוֹן־יְרֵאָיו יַעֲשֶׂה וְאֶת־שַׁוְעָתָם יִשְׁמַע וְיוֹשִׁיעֵם",
    20: "שׁוֹמֵר יְהוָה אֶת־כׇּל־אֹהֲבָיו וְאֵת כׇּל־הָרְשָׁעִים יַשְׁמִיד",
    21: "תְּהִלַּת יְהוָה יְדַבֶּר־פִּי וִיבָרֵךְ כׇּל־בָּשָׂר שֵׁם קׇדְשׁוֹ לְעוֹלָם וָעֶד",
}


class TestPhoneticAnalyst(unittest.TestCase):
    """
    Unit tests for the PhoneticAnalyst.
    """

    def setUp(self):
        """Set up the test case."""
        self.analyst = PhoneticAnalyst()

    def test_psalm_145_transcription(self):
        """
        Test the transcription of the entirety of Psalm 145.
        This test will print the output for manual verification for now.
        In the future, we can assert against a known-good JSON output.
        """
        print("\n--- Testing Full Transcription of Psalm 145 ---")
        
        full_psalm_analysis = {}
        for verse_num, verse_text in PSALM_145_HEBREW.items():
            with self.subTest(verse=verse_num):
                # This is where the magic happens
                analysis = self.analyst.transcribe_verse(verse_text)
                
                # Basic validation
                self.assertIn("original_text", analysis)
                self.assertIn("words", analysis)
                self.assertEqual(analysis["original_text"], verse_text)
                self.assertIsInstance(analysis["words"], list)
                
                full_psalm_analysis[verse_num] = analysis

        # Pretty-print the entire analysis for review
        # In a real-world scenario, you might save this to a file or compare hashes
        output_path = "test_output_psalm145.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(full_psalm_analysis, f, indent=2, ensure_ascii=False)
            
        print(f"Full analysis of Psalm 145 has been written to {output_path}")
        print("Please review the file to verify correctness of the placeholder transcription.")


if __name__ == '__main__':
    unittest.main()
