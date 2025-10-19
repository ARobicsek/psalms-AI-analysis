# Rate Limiting Guide for Phase 4 Pipeline

**Updated:** 2025-10-18
**Phase:** 4 - Enhanced Pipeline with Master Editor

---

## TL;DR

**Default delay: 120 seconds** between pipeline steps (up from 90 seconds in Phase 3)

This is necessary due to the addition of the Master Editor (GPT-5) which uses ~50K tokens.

---

## Anthropic Rate Limits

### Current Limits (as of 2025-10)

**Token Bucket Model:**
- **Rate limit:** 30,000 input tokens per minute
- **Refill rate:** 500 tokens per second
- **Bucket size:** 30,000 tokens

**What this means:**
- You can send 30K tokens immediately
- After that, the bucket refills at 500 tokens/second
- To fully refill: 30,000 ÷ 500 = 60 seconds

**Key insight:** If you use 30K tokens, you need to wait AT LEAST 60 seconds before the next 30K token request.

---

## Phase 4 Token Usage Per Psalm

### Per-Step Breakdown

| Step | Model | Tokens | Delay After |
|------|-------|--------|-------------|
| 1. MacroAnalyst | Sonnet 4.5 | ~5K | 120s ✅ |
| 2. MicroAnalyst | Sonnet 4.5 | ~15K | 120s ✅ |
| 3. SynthesisWriter (intro) | Sonnet 4.5 | ~25K | (internal) |
| 3. SynthesisWriter (verses) | Sonnet 4.5 | ~30K | 120s ✅ |
| 4. MasterEditor | GPT-5 | ~50K | 120s ✅ |
| 5. Print-Ready | N/A (local) | 0 | 0s |

**Total API tokens:** ~125K across 4 API-heavy steps

### Why 120 Seconds?

**Phase 3 (90 seconds):**
- Total: ~75K tokens (macro + micro + synthesis)
- 90 seconds allows 45K tokens to refill
- This was sufficient

**Phase 4 (120 seconds):**
- Total: ~125K tokens (macro + micro + synthesis + master edit)
- Master Editor alone: ~50K tokens
- 120 seconds allows 60K tokens to refill
- **Safety margin for:**
  - Longer psalms (more verses = more tokens)
  - Network delays
  - API processing time
  - Research bundle size variations

---

## Delay Settings

### Default (Recommended)

```bash
python scripts/run_enhanced_pipeline.py 23
# Uses 120-second default delay
```

**Per-psalm duration:** ~8-10 minutes
- MacroAnalyst: ~30s + 120s delay
- MicroAnalyst: ~60s + 120s delay
- SynthesisWriter: ~90-120s + 120s delay
- MasterEditor: ~2-5 minutes + 120s delay
- Print-Ready: ~5s

**Total:** ~8-10 minutes per psalm

### Conservative (Extra Safe)

```bash
python scripts/run_enhanced_pipeline.py 51 --delay 150
```

**When to use:**
- Longer psalms (20+ verses)
- Network instability
- Multiple concurrent users on same API key
- Being extra cautious

**Per-psalm duration:** ~10-12 minutes

### Aggressive (Faster, Riskier)

```bash
python scripts/run_enhanced_pipeline.py 23 --delay 90
```

**When to use:**
- Short psalms (6-8 verses)
- Testing/development
- Single user, stable connection
- Willing to retry on rate limit errors

**Risk:** May hit rate limits on longer psalms

**Per-psalm duration:** ~6-8 minutes

---

## Rate Limit Errors

### What They Look Like

```
anthropic.RateLimitError: Error code: 429 -
{'type': 'error', 'error': {'type': 'rate_limit_error',
'message': 'Request too large for current usage tier.
Please wait before retrying.'}}
```

### How to Handle

1. **Automatic retry** - The pipeline doesn't auto-retry (by design)
2. **Manual fix:**
   ```bash
   # Resume from where it failed using skip flags
   python scripts/run_enhanced_pipeline.py 23 \
     --skip-macro --skip-micro \
     --delay 150
   ```

3. **Prevention:**
   - Use longer delays (150s for safety)
   - Process psalms sequentially (not parallel)
   - Avoid running multiple pipelines simultaneously

---

## Batch Processing Considerations

### Sequential Processing

**Recommended approach for 3-5 test psalms:**

```bash
# Process Psalm 23
python scripts/run_enhanced_pipeline.py 23 --delay 120

# Wait for completion (~8-10 minutes)
# Then process Psalm 1
python scripts/run_enhanced_pipeline.py 1 --delay 120

# Wait for completion
# Then process Psalm 51
python scripts/run_enhanced_pipeline.py 51 --delay 120
```

**Total time for 3 psalms:** ~24-30 minutes

### Parallel Processing

**NOT RECOMMENDED** - Will hit rate limits

```bash
# DON'T DO THIS
python scripts/run_enhanced_pipeline.py 23 &
python scripts/run_enhanced_pipeline.py 1 &
python scripts/run_enhanced_pipeline.py 51 &
# All will fail with rate limit errors
```

### Full Production (150 Psalms)

**Option A: Sequential with delays**
- Duration: 150 × 10 min = 1,500 minutes = **25 hours**
- Cost: ~$91-129 (without batch API discount)
- Simple, reliable

**Option B: Anthropic Message Batches API** ✅ RECOMMENDED
- Pre-generate all macro/micro/research
- Submit 300 synthesis requests (150 intro + 150 verses) as batch
- Master edit sequentially after
- Duration: ~24 hours for synthesis batch + ~25 hours for master editing = **~2 days**
- Cost: ~$60-85 (50% off synthesis, full price master edit)
- Most efficient

---

## Monitoring Token Usage

### Log Output

The pipeline logs token usage for each step:

```
[STEP 1] Running MacroAnalyst...
  ✓ Macro analysis complete
  Input tokens: 4,532

[STEP 2] Running MicroAnalyst v2...
  ✓ Micro analysis complete
  Input tokens: 14,721

[STEP 3] Running SynthesisWriter...
  ✓ Introduction complete
  Input tokens: 23,456
  ✓ Verse commentary complete
  Input tokens: 28,943

[STEP 4] Running MasterEditor...
  ✓ Editorial review complete
  Input tokens: 51,234
```

### Tracking Over Time

For production runs, monitor cumulative token usage to estimate:
- Total cost
- Completion time
- Rate limit buffer remaining

---

## Best Practices

### For Testing (3-5 Psalms)

✅ **DO:**
- Use default 120-second delay
- Process sequentially
- Monitor logs for token usage
- Test on diverse psalm lengths

❌ **DON'T:**
- Run psalms in parallel
- Reduce delay below 90 seconds
- Skip monitoring first few runs

### For Production (150 Psalms)

✅ **DO:**
- Use Message Batches API for synthesis
- Pre-generate all macro/micro/research files
- Sequential master editing with 120s delays
- Consider 150s delays for extra safety

❌ **DON'T:**
- Try to parallelize without batch API
- Rush the process
- Reduce delays to save time (costs more in retries)

---

## Troubleshooting

### "Still hitting rate limits with 120s delay"

**Possible causes:**
1. Longer psalm (20+ verses) → Use `--delay 150`
2. Large research bundle → Normal, increase delay
3. Multiple API keys on same account → Consolidate
4. Network delays → Increase delay buffer

### "Pipeline is too slow"

**Solutions:**
1. Accept the slowness (safety first)
2. Use batch API for production
3. Process only high-priority psalms
4. Run overnight/background

### "Can I speed it up safely?"

**Yes, if:**
- Testing short psalms (6-8 verses) → Try `--delay 90`
- Stable network connection
- Single user on API key
- Willing to retry if needed

**No, if:**
- Long psalms (15+ verses)
- Production run
- Shared API key
- Need reliability > speed

---

## Summary

**Default: 120 seconds** - Safe, reliable, recommended

**Formula:**
```
Per-psalm time = 8-10 minutes
Full 150 psalms = ~25 hours sequential (or ~2 days with batch API)
```

**Key takeaway:** The delays are there to prevent errors and ensure quality. Don't try to optimize them away unless you're willing to handle rate limit retries manually.

---

**Questions?** See [docs/QUICK_START_PHASE4.md](QUICK_START_PHASE4.md) for usage examples.
