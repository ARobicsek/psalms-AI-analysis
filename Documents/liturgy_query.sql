select 
pli.index_id,
pli.psalm_chapter,
pli.psalm_verse_start,
pli.psalm_verse_end,
pli.psalm_phrase_hebrew,
pli.prayer_id,
pli.liturgy_context,
hebrew_text,
pli.match_type,
confidence,
distinctiveness_score,
source_text,
canonical_prayer_name,
canonical_L1_Occasion,
canonical_L2_Service,
canonical_L3_Signpost,
canonical_L4_SubSection,
canonical_location_description
from psalms_liturgy_index pli
inner join prayers pr
where pli.prayer_id=pr.prayer_id
--and pli.prayer_id=625
--and canonical_location_description like '%Psalm%'
and psalm_chapter=23
order by psalm_chapter,psalm_verse_start
