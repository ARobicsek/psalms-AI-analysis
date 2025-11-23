# PRIMARY CARE INSIGHTS BANK - NEXT SESSION PROMPT

## OBJECTIVE
Create a complete Primary Care Insights Bank document with 10 comprehensive use cases matching the quality of the existing Cardiology document.

## FILES PREPARED FOR YOU

### Source Documents (Extracted)
- `cordance_work_in_progress.txt` - Contains 1 complete Primary Care use case + 4 incomplete ones
- `cordance_gemini_ideas.txt` - Contains 5 new Primary Care use case ideas
- `cordance_cardiology.txt` - Benchmark document showing quality/formatting standards
- `cordance_claude_ideas.txt` - Additional use case ideas for reference

### Research Completed
- `PRIMARY_CARE_RESEARCH_NOTES.md` - Comprehensive PubMed search findings with citations

## THE 10 USE CASES TO CREATE

### ✅ From Work-in-Progress (1 complete, 4 to expand):
1. **Comprehensive Preventive Care Optimization** - COMPLETE (use as reference model)
2. **Diabetes Comprehensive Management** - Expand from 1 paragraph to full use case
3. **Chronic Kidney Disease Early Detection** - Expand from 1 paragraph to full use case
4. **Polypharmacy Optimization and Deprescribing** - Expand from 1 paragraph to full use case
5. **SDOH Identification and Community Resource Connection** - Expand from 1 paragraph to full use case

### 🆕 From Gemini Ideas (create from scratch):
6. **Colonoscopy Referral Retention** - Keep screening colonoscopies in-network
7. **Lower Back Pain Imaging Stewardship** - Divert from premature MRI to PT
8. **HCC Coding Optimization** - Accurate risk adjustment coding
9. **Pre-operative Clearance Optimization** - Prevent OR cancellations
10. **Generic/Biosimilar Therapeutic Interchange** - Real-time cost-saving switches

## REQUIRED STRUCTURE FOR EACH USE CASE

```
USE CASE [N]: [Title]

Clinical Scenario
[1 paragraph describing realistic patient encounter]

Current State Challenges
At a practice level:
- [3-4 bullets with statistics/citations]

At the individual patient level:
- [3-4 bullets describing pain points]

Cordance Solution

Before Encounter
- [3-4 bullets on proactive preparation]

During Encounter
- [5-7 bullets on real-time decision support]

After Encounter
- [3-5 bullets on automation/follow-up]

Impact on Three Pillars

Economics (Value-Based Care & Fee-for-Service)
- [4-5 bullets with financial impacts, cited]
- Final bullet: "Estimated financial impact: $X-$Y annually per PCP..."

Quality & Safety
- [4-5 bullets with clinical outcomes + PubMed citations]

Population Health & Outcomes
- [4-5 bullets on systematic improvements]
- Final bullet: "Estimated impact: [specific metric]..."

Physician Value Proposition
- [4-6 bullets on workflow benefits]

Implementation Considerations
- [3-5 bullets on technical/operational requirements]
```

## FORMATTING REQUIREMENTS (CRITICAL!)

### Headers - All in Blue (#1F4E78):
- **H1**: "Primary Care" (32pt, bold)
- **H2**: Use case titles (28pt, bold)
- **H3**: "Clinical Scenario", "Current State Challenges", etc. (26pt, bold)
- **H4**: "Before Encounter", "During Encounter", "After Encounter", "Economics", etc. (24pt, bold)
- **Use normal case, NOT ALL CAPS** (e.g., "Quality & Safety" not "QUALITY & SAFETY")

### Spacing:
- **0pt before and 0pt after** for ALL paragraphs - absolutely critical
- Let Word handle line wrapping naturally
- NO manual line breaks within paragraphs

### Font & Bullets:
- Arial 12pt throughout
- Proper Word bullet lists, NOT unicode symbols

## CLINICAL EVIDENCE - RESEARCH COMPLETED

See `PRIMARY_CARE_RESEARCH_NOTES.md` for detailed findings on:

### Diabetes Management:
- GLP-1 RA reduces HbA1c ~0.8-1.0% and cardiovascular events by 20%
- SGLT2i reduces heart failure hospitalization by 26%
- Meta-analysis showing MACE benefit with HbA1c reduction

### CKD Prevention:
- SGLT2i reduces CKD progression by 37-39%
- eGFR decline slowed from -4.7 to -3.5 mL/min/1.73m²/year
- ESRD costs: $76,969 annually vs $7,537 for no CKD

### Polypharmacy:
- >40% of older adults affected
- Beers Criteria 2023 update available
- Level 2 anticholinergic drugs increase fall risk by 56%
- Hip fracture costs: $30K-$60K per event

### SDOH:
- SDOH affects 50% of health outcomes vs 20% for clinical care
- Food insecurity linked to 56% higher fair/poor health
- 60% higher developmental delay risk in children

### Colonoscopy:
- Only 59% of eligible patients up-to-date
- FIT test users 33% less likely to die from CRC
- Follow-up colonoscopy critical within 6 months of positive FIT

### Lower Back Pain:
- 31% of lumbar spine MRIs inappropriate per CMS criteria
- Early imaging increases 1-year costs by $4,700
- Physical therapy first reduces surgery, injections, ED visits

### HCC Coding:
- RAF score predicts healthcare costs (1.0 = average)
- $377M lost annually from coding inaccuracies
- RADV penalties multiply by 55x across population
- Chronic conditions must be recaptured annually

### Pre-operative:
- RCRI predicts cardiac complications (0-3+ risk factors)
- Complications: 0.4% (0 factors) to 11% (3+ factors)
- Assess as "risk stratification" not "clearance"

### Biosimilars:
- $56B in healthcare savings since 2015
- 50-60% cheaper than reference biologics
- 80% adherence improvement with interchange programs

### Diabetic Retinopathy:
- Leading cause of blindness in working-age adults
- Type 1: Screen within 3-5 years of diagnosis
- Type 2: Screen at diagnosis
- Annual exams reduce vision loss substantially

## TECHNICAL IMPLEMENTATION

### Use docx Library:
```javascript
const { Document, Paragraph, TextRun, AlignmentType, HeadingLevel } = require('docx');

// Helper functions needed:
function h1(text) { /* 32pt, blue, bold */ }
function h2(text) { /* 28pt, blue, bold */ }
function h3(text) { /* 26pt, blue, bold */ }
function h4(text) { /* 24pt, blue, bold */ }
function p(text) { /* 12pt, Arial, 0pt spacing */ }
function bullet(text) { /* Bullet list item */ }
function bulletWithRef(text, citation) { /* Bullet with superscript reference */ }
```

### Output Location:
`docs/Cordance/Cordance_Health_Insights_Bank_Primary_Care.docx`

### Reference Format:
```
[1] Author et al. Title. Journal. Year;Vol(Issue):Pages. https://doi.org/XX.XXXX/xxxxx
```

## QUALITY BENCHMARKS

Each use case should be:
- **2-3 pages** of substantive content
- **Evidence-based** with recent PubMed citations (prefer 2020+)
- **Realistic** clinical scenarios authentic to primary care
- **Specific** with concrete numbers, percentages, dollar amounts
- **Actionable** with clear value propositions

Target: **25-35 total PubMed references** across all 10 use cases.

## SUCCESS CRITERIA

The final document should:
1. Match the Cardiology document's professional quality
2. Have perfect formatting (blue headers, 0pt spacing, Arial font)
3. Include comprehensive clinical evidence with active DOI links
4. Provide specific, quantified impacts for each use case
5. Be immediately ready for Duke and UMass clinician review

## NEXT STEPS

1. Read `PRIMARY_CARE_RESEARCH_NOTES.md` for all clinical evidence
2. Read `cordance_work_in_progress.txt` lines 865-1270 for Primary Care content
3. Read `cordance_gemini_ideas.txt` lines 255-379 for the 5 new use case ideas
4. Create `generate_primary_care_insights.js` with all 10 use cases
5. Run: `node generate_primary_care_insights.js`
6. Output: `docs/Cordance/Cordance_Health_Insights_Bank_Primary_Care.docx`

## ESTIMATED TIME
2-3 hours to create comprehensive JavaScript file with all content and references.

---
**Session prepared by:** Claude (Session 138)
**Date:** 2025-11-23
**Branch:** claude/primary-care-insights-bank-01WNTbHdGcHrYJ5SgNBfCTTd
