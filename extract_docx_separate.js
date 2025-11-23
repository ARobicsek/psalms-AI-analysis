const mammoth = require('mammoth');
const fs = require('fs');

async function extractDocx(filePath, outputPath) {
    try {
        const result = await mammoth.extractRawText({path: filePath});
        fs.writeFileSync(outputPath, result.value, 'utf-8');
        console.log(`Extracted ${filePath} -> ${outputPath}`);
    } catch (error) {
        console.error(`Error extracting ${filePath}:`, error);
    }
}

async function main() {
    await extractDocx(
        'docs/Cordance/Work in progress Cordance_Health_Insights_Bank.docx',
        'cordance_work_in_progress.txt'
    );
    await extractDocx(
        'docs/Cordance/Insights ideas Gemini 3.docx',
        'cordance_gemini_ideas.txt'
    );
    await extractDocx(
        'docs/Cordance/Cordance_Health_Insights_Bank_Cardiology.docx',
        'cordance_cardiology.txt'
    );
    await extractDocx(
        'docs/Cordance/Insights ideas Claude Sonnet 4.5.docx',
        'cordance_claude_ideas.txt'
    );
}

main();
