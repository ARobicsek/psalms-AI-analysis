# Top 100 Psalm Connections - Enhanced Scoring System

**Generated**: 2025-11-13 21:44:45

## Methodology

This report uses an enhanced scoring system that combines:

1. **Contiguous phrases** (2, 3, 4+ words)
2. **Skip-gram patterns** (non-contiguous patterns within windows)
3. **Root IDF overlap** (rarity-weighted vocabulary sharing)
4. **Length normalization** (adjusted for psalm word counts)

### Scoring Formula

```
pattern_points = (2-word × 1) + (3-word × 2) + (4+ word × 3)
root_idf_sum = sum of IDF scores for shared roots
geom_mean_length = sqrt(word_count_A × word_count_B)

phrase_score = (pattern_points / geom_mean_length) × 1000
root_score = (root_idf_sum / geom_mean_length) × 1000

FINAL_SCORE = phrase_score + root_score
```

## Score Statistics

- **Minimum score**: 7.33
- **Maximum score**: 100864.09
- **Median score**: 149.07
- **Top 100 threshold**: 555.16
- **Top 150 threshold**: 457.71

## Validation: Known Connections

| Psalms | Description | New Rank | Score | Old Rank | Status |
|--------|-------------|----------|-------|----------|--------|
| 14 & 53 | Nearly identical Psalms | #2 | 93127.47 | #1 | ✓ |
| 60 & 108 | Composite Psalm (57+60) | #1 | 100864.09 | #2 | ✓ |
| 40 & 70 | Shared passage | #3 | 36394.51 | #3 | ✓ |
| 42 & 43 | Originally one Psalm | #5 | 28021.98 | #195 | ✓ |
| 25 & 34 | Thematic connection (scholarly consensus) | #309 | 359.50 | #123 | ✗ |

## Top 100 Connections

| Rank | Psalms | Score | Patterns | Roots | Old Rank | Change |
|------|--------|-------|----------|-------|----------|--------|
| 1 | 60 & 108 | 100864.09 | 11030 | 54 | 2 | +1 ↑ |
| 2 | 14 & 53 | 93127.47 | 7090 | 45 | 1 | -1 ↓ |
| 3 | 40 & 70 | 36394.51 | 3592 | 38 | 3 | = |
| 4 | 57 & 108 | 28520.03 | 3005 | 27 | 38 | +34 ↑ |
| 5 | 42 & 43 | 28021.98 | 2648 | 19 | 195 | +190 ↑ |
| 6 | 115 & 135 | 19464.78 | 2941 | 38 | 5 | -1 ↓ |
| 7 | 96 & 98 | 8183.72 | 744 | 25 | 21 | +14 ↑ |
| 8 | 29 & 96 | 5733.55 | 577 | 15 | 1380 | +1372 ↑ |
| 9 | 31 & 71 | 4633.59 | 939 | 52 | 6 | -3 ↓ |
| 10 | 113 & 135 | 3336.21 | 335 | 17 | 1189 | +1179 ↑ |
| 11 | 118 & 136 | 2651.59 | 467 | 18 | 2514 | +2503 ↑ |
| 12 | 134 & 135 | 2356.58 | 147 | 14 | 541 | +529 ↑ |
| 13 | 93 & 96 | 1748.21 | 110 | 13 | 1740 | +1727 ↑ |
| 14 | 83 & 97 | 1688.02 | 170 | 19 | 2521 | +2507 ↑ |
| 15 | 35 & 70 | 1568.71 | 123 | 29 | 16 | +1 ↑ |
| 16 | 47 & 49 | 1540.31 | 168 | 15 | 4155 | +4139 ↑ |
| 17 | 124 & 134 | 1500.49 | 55 | 7 | 5565 | +5548 ↑ |
| 18 | 113 & 148 | 1496.22 | 115 | 16 | 938 | +920 ↑ |
| 19 | 6 & 12 | 1403.42 | 109 | 11 | 7072 | +7053 ↑ |
| 20 | 79 & 89 | 1352.03 | 266 | 37 | 617 | +597 ↑ |
| 21 | 117 & 146 | 1297.98 | 49 | 8 | 3744 | +3723 ↑ |
| 22 | 47 & 97 | 1250.99 | 97 | 16 | 1284 | +1262 ↑ |
| 23 | 48 & 97 | 1205.64 | 104 | 21 | 697 | +674 ↑ |
| 24 | 121 & 131 | 1204.71 | 46 | 12 | 681 | +657 ↑ |
| 25 | 6 & 38 | 1124.71 | 103 | 25 | 273 | +248 ↑ |
| 26 | 130 & 131 | 1124.34 | 42 | 9 | 3372 | +3346 ↑ |
| 27 | 135 & 136 | 1093.62 | 143 | 28 | 48 | +21 ↑ |
| 28 | 135 & 148 | 1088.38 | 128 | 24 | 340 | +312 ↑ |
| 29 | 127 & 131 | 1069.87 | 48 | 6 | 8930 | +8901 ↑ |
| 30 | 54 & 86 | 1059.92 | 70 | 25 | 43 | +13 ↑ |
| 31 | 113 & 117 | 1040.04 | 31 | 8 | 2677 | +2646 ↑ |
| 32 | 128 & 134 | 1008.89 | 28 | 8 | 3577 | +3545 ↑ |
| 33 | 57 & 59 | 963.03 | 102 | 21 | 1345 | +1312 ↑ |
| 34 | 106 & 136 | 939.90 | 186 | 27 | 1260 | +1226 ↑ |
| 35 | 106 & 118 | 925.75 | 196 | 33 | 1239 | +1204 ↑ |
| 36 | 41 & 106 | 917.43 | 156 | 28 | 2380 | +2344 ↑ |
| 37 | 116 & 117 | 912.08 | 43 | 7 | 6726 | +6689 ↑ |
| 38 | 47 & 83 | 908.40 | 77 | 19 | 982 | +944 ↑ |
| 39 | 135 & 147 | 906.12 | 95 | 35 | 33 | -6 ↓ |
| 40 | 148 & 150 | 895.36 | 53 | 4 | 10837 | +10797 ↑ |
| 41 | 86 & 103 | 889.32 | 111 | 26 | 369 | +328 ↑ |
| 42 | 135 & 146 | 869.74 | 90 | 20 | 955 | +913 ↑ |
| 43 | 28 & 143 | 858.62 | 68 | 21 | 434 | +391 ↑ |
| 44 | 121 & 134 | 851.11 | 24 | 12 | 373 | +329 ↑ |
| 45 | 95 & 96 | 845.11 | 72 | 17 | 1328 | +1283 ↑ |
| 46 | 67 & 76 | 841.13 | 47 | 14 | 1383 | +1337 ↑ |
| 47 | 96 & 97 | 830.96 | 59 | 22 | 167 | +120 ↑ |
| 48 | 107 & 118 | 812.75 | 152 | 30 | 1309 | +1261 ↑ |
| 49 | 106 & 107 | 809.30 | 169 | 47 | 516 | +467 ↑ |
| 50 | 111 & 112 | 795.51 | 41 | 15 | 1485 | +1435 ↑ |
| 51 | 79 & 115 | 793.33 | 85 | 22 | 1003 | +952 ↑ |
| 52 | 125 & 128 | 792.20 | 26 | 11 | 2129 | +2077 ↑ |
| 53 | 116 & 135 | 791.09 | 92 | 23 | 800 | +747 ↑ |
| 54 | 134 & 146 | 790.29 | 34 | 9 | 3688 | +3634 ↑ |
| 55 | 56 & 118 | 789.29 | 105 | 18 | 3454 | +3399 ↑ |
| 56 | 8 & 84 | 760.68 | 52 | 16 | 2459 | +2403 ↑ |
| 57 | 113 & 121 | 760.42 | 35 | 13 | 1200 | +1143 ↑ |
| 58 | 47 & 85 | 733.49 | 49 | 17 | 773 | +715 ↑ |
| 59 | 100 & 118 | 732.75 | 57 | 15 | 1811 | +1752 ↑ |
| 60 | 35 & 40 | 729.98 | 95 | 42 | 55 | -5 ↓ |
| 61 | 98 & 100 | 727.34 | 26 | 16 | 296 | +235 ↑ |
| 62 | 57 & 58 | 721.95 | 57 | 14 | 5580 | +5518 ↑ |
| 63 | 124 & 129 | 717.36 | 31 | 10 | 3834 | +3771 ↑ |
| 64 | 47 & 96 | 690.30 | 54 | 15 | 1494 | +1430 ↑ |
| 65 | 8 & 12 | 669.61 | 47 | 12 | 5438 | +5373 ↑ |
| 66 | 113 & 134 | 662.98 | 22 | 9 | 2483 | +2417 ↑ |
| 67 | 44 & 79 | 660.08 | 61 | 31 | 484 | +417 ↑ |
| 68 | 8 & 9 | 659.47 | 54 | 19 | 2006 | +1938 ↑ |
| 69 | 6 & 31 | 658.80 | 53 | 28 | 203 | +134 ↑ |
| 70 | 117 & 135 | 655.10 | 32 | 9 | 3714 | +3644 ↑ |
| 71 | 32 & 64 | 654.10 | 43 | 16 | 3332 | +3261 ↑ |
| 72 | 27 & 143 | 653.45 | 61 | 28 | 133 | +61 ↑ |
| 73 | 6 & 8 | 643.76 | 44 | 11 | 6882 | +6809 ↑ |
| 74 | 27 & 102 | 641.58 | 69 | 35 | 117 | +43 ↑ |
| 75 | 113 & 146 | 640.51 | 38 | 12 | 3320 | +3245 ↑ |
| 76 | 148 & 149 | 633.65 | 39 | 16 | 1575 | +1499 ↑ |
| 77 | 117 & 148 | 627.30 | 24 | 9 | 2792 | +2715 ↑ |
| 78 | 47 & 95 | 622.72 | 44 | 12 | 4540 | +4462 ↑ |
| 79 | 124 & 131 | 621.92 | 24 | 8 | 4765 | +4686 ↑ |
| 80 | 106 & 147 | 615.66 | 89 | 36 | 899 | +819 ↑ |
| 81 | 49 & 85 | 611.32 | 52 | 23 | 767 | +686 ↑ |
| 82 | 121 & 124 | 605.60 | 26 | 11 | 2576 | +2494 ↑ |
| 83 | 104 & 117 | 604.53 | 38 | 8 | 8039 | +7956 ↑ |
| 84 | 95 & 135 | 603.49 | 58 | 19 | 1744 | +1660 ↑ |
| 85 | 25 & 143 | 600.77 | 49 | 30 | 56 | -29 ↓ |
| 86 | 58 & 59 | 597.01 | 56 | 16 | 6623 | +6537 ↑ |
| 87 | 84 & 85 | 590.16 | 43 | 21 | 526 | +439 ↑ |
| 88 | 35 & 38 | 586.29 | 62 | 40 | 79 | -9 ↓ |
| 89 | 98 & 149 | 584.50 | 23 | 15 | 1392 | +1303 ↑ |
| 90 | 113 & 131 | 583.49 | 22 | 8 | 5052 | +4962 ↑ |
| 91 | 6 & 28 | 583.26 | 43 | 12 | 6089 | +5998 ↑ |
| 92 | 100 & 136 | 570.71 | 39 | 14 | 1299 | +1207 ↑ |
| 93 | 96 & 149 | 570.66 | 25 | 19 | 262 | +169 ↑ |
| 94 | 78 & 105 | 566.38 | 41 | 93 | 4 | -90 ↓ |
| 95 | 75 & 76 | 565.03 | 41 | 13 | 5648 | +5553 ↑ |
| 96 | 147 & 149 | 565.00 | 32 | 17 | 2616 | +2520 ↑ |
| 97 | 96 & 99 | 560.35 | 35 | 18 | 508 | +411 ↑ |
| 98 | 104 & 146 | 558.52 | 64 | 25 | 1131 | +1033 ↑ |
| 99 | 107 & 136 | 557.29 | 104 | 20 | 4463 | +4364 ↑ |
| 100 | 5 & 138 | 555.16 | 34 | 18 | 1307 | +1207 ↑ |

## Detailed Breakdown: Top 10

### 1. Psalms 60 & 108

**Final Score**: 100864.09

**Pattern Analysis**:
- Contiguous phrases: 2w=46, 3w=36, 4+w=0
- Skip-grams: 2w=208, 3w=666, 4w=3124
- **Total pattern points**: 11030

**Root Analysis**:
- Shared roots: 54
- Root IDF sum: 136.80

**Normalization**:
- Psalm 60 length: 119 words
- Psalm 108 length: 103 words
- Geometric mean: 110.7

**Component Scores**:
- Phrase score: 99628.46
- Root score: 1235.63

### 2. Psalms 14 & 53

**Final Score**: 93127.47

**Pattern Analysis**:
- Contiguous phrases: 2w=42, 3w=31, 4+w=0
- Skip-grams: 2w=170, 3w=474, 4w=1956
- **Total pattern points**: 7090

**Root Analysis**:
- Shared roots: 45
- Root IDF sum: 78.40

**Normalization**:
- Psalm 14 length: 75 words
- Psalm 53 length: 79 words
- Geometric mean: 77.0

**Component Scores**:
- Phrase score: 92109.00
- Root score: 1018.47

### 3. Psalms 40 & 70

**Final Score**: 36394.51

**Pattern Analysis**:
- Contiguous phrases: 2w=26, 3w=14, 4+w=0
- Skip-grams: 2w=108, 3w=266, 4w=966
- **Total pattern points**: 3592

**Root Analysis**:
- Shared roots: 38
- Root IDF sum: 74.46

**Normalization**:
- Psalm 40 length: 199 words
- Psalm 70 length: 51 words
- Geometric mean: 100.7

**Component Scores**:
- Phrase score: 35655.35
- Root score: 739.16

### 4. Psalms 57 & 108

**Final Score**: 28520.03

**Pattern Analysis**:
- Contiguous phrases: 2w=20, 3w=13, 4+w=0
- Skip-grams: 2w=84, 3w=227, 4w=807
- **Total pattern points**: 3005

**Root Analysis**:
- Shared roots: 27
- Root IDF sum: 44.51

**Normalization**:
- Psalm 57 length: 111 words
- Psalm 108 length: 103 words
- Geometric mean: 106.9

**Component Scores**:
- Phrase score: 28103.76
- Root score: 416.27

### 5. Psalms 42 & 43

**Final Score**: 28021.98

**Pattern Analysis**:
- Contiguous phrases: 2w=16, 3w=11, 4+w=0
- Skip-grams: 2w=65, 3w=179, 4w=729
- **Total pattern points**: 2648

**Root Analysis**:
- Shared roots: 19
- Root IDF sum: 32.75

**Normalization**:
- Psalm 42 length: 143 words
- Psalm 43 length: 64 words
- Geometric mean: 95.7

**Component Scores**:
- Phrase score: 27679.61
- Root score: 342.37

### 6. Psalms 115 & 135

**Final Score**: 19464.78

**Pattern Analysis**:
- Contiguous phrases: 2w=27, 3w=19, 4+w=0
- Skip-grams: 2w=96, 3w=235, 4w=770
- **Total pattern points**: 2941

**Root Analysis**:
- Shared roots: 38
- Root IDF sum: 57.84

**Normalization**:
- Psalm 115 length: 138 words
- Psalm 135 length: 172 words
- Geometric mean: 154.1

**Component Scores**:
- Phrase score: 19089.36
- Root score: 375.42

### 7. Psalms 96 & 98

**Final Score**: 8183.72

**Pattern Analysis**:
- Contiguous phrases: 2w=15, 3w=8, 4+w=0
- Skip-grams: 2w=47, 3w=75, 4w=172
- **Total pattern points**: 744

**Root Analysis**:
- Shared roots: 25
- Root IDF sum: 39.42

**Normalization**:
- Psalm 96 length: 116 words
- Psalm 98 length: 79 words
- Geometric mean: 95.7

**Component Scores**:
- Phrase score: 7771.96
- Root score: 411.76

### 8. Psalms 29 & 96

**Final Score**: 5733.55

**Pattern Analysis**:
- Contiguous phrases: 2w=8, 3w=5, 4+w=0
- Skip-grams: 2w=27, 3w=53, 4w=142
- **Total pattern points**: 577

**Root Analysis**:
- Shared roots: 15
- Root IDF sum: 21.71

**Normalization**:
- Psalm 29 length: 94 words
- Psalm 96 length: 116 words
- Geometric mean: 104.4

**Component Scores**:
- Phrase score: 5525.64
- Root score: 207.91

### 9. Psalms 31 & 71

**Final Score**: 4633.59

**Pattern Analysis**:
- Contiguous phrases: 2w=12, 3w=6, 4+w=0
- Skip-grams: 2w=46, 3w=82, 4w=235
- **Total pattern points**: 939

**Root Analysis**:
- Shared roots: 52
- Root IDF sum: 84.51

**Normalization**:
- Psalm 31 length: 228 words
- Psalm 71 length: 214 words
- Geometric mean: 220.9

**Component Scores**:
- Phrase score: 4251.00
- Root score: 382.59

### 10. Psalms 113 & 135

**Final Score**: 3336.21

**Pattern Analysis**:
- Contiguous phrases: 2w=9, 3w=4, 4+w=0
- Skip-grams: 2w=24, 3w=36, 4w=74
- **Total pattern points**: 335

**Root Analysis**:
- Shared roots: 17
- Root IDF sum: 15.03

**Normalization**:
- Psalm 113 length: 64 words
- Psalm 135 length: 172 words
- Geometric mean: 104.9

**Component Scores**:
- Phrase score: 3192.94
- Root score: 143.27
