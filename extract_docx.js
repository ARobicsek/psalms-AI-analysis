const mammoth = require('mammoth');
const fs = require('fs');
const path = require('path');

async function extractDocx(filePath) {
    try {
        const result = await mammoth.extractRawText({path: filePath});
        return result.value;
    } catch (error) {
        console.error(`Error extracting ${filePath}:`, error);
        return null;
    }
}

async function main() {
    const files = [
        'docs/Cordance/Work in progress Cordance_Health_Insights_Bank.docx',
        'docs/Cordance/Insights ideas Gemini 3.docx',
        'docs/Cordance/Cordance_Health_Insights_Bank_Cardiology.docx',
        'docs/Cordance/Insights ideas Claude Sonnet 4.5.docx'
    ];

    for (const file of files) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`FILE: ${file}`);
        console.log('='.repeat(80));
        const text = await extractDocx(file);
        if (text) {
            console.log(text);
        }
        console.log('\n');
    }
}

main();
