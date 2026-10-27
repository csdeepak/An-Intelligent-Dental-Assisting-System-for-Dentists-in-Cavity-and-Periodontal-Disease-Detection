# Open issues: mentor draft, v002 (review round v001_1)

## Must resolve before any submission
- [MISSING RESULT] Paired CIs for constant-minus-pipeline on DENTEX, Ningxia pooled and CariesXrays (no saved artifact; Q-008 chose to omit). Also per-site intervals for the constant and lesion detector on Ningxia (inference:4 / selective_presentation). Regenerate with the project's bootstrap script and save the output.
- [ASK AUTHOR] Public anchor for the lesion-detector pre-registration (currently commit ef3f453 of a private repository) (finding:28, evidence_traceability).
- [ASK AUTHOR] VLM decoding settings (sampling, max tokens) not recorded in the artifact (finding:11).
- [CITATION NEEDED] Gap statement: systematic count of image-blind baselines / external validation in OPG caries papers (the project's "2 of 49" count has no saved script; Q-010 omitted it).
- ECE has no interval (finding:10); a bootstrap over the 34 source images would add one.
- Position-only control for numbering and confidence (finding:33 / inference:2) -- an experiment, not a wording fix.
- Title scope (inference:1 / overgeneralization): the reviewer notes the title "What a Tooth-Level Score Cannot Tell You" is broader than the evidence, since the same metric separated the lesion detector. Title kept per Q-001 (author's own title); the text now scopes the claim to the gate-variant pipeline. Mentor/author decision.
- Author and affiliation block; acknowledgment/AI-disclosure wording ([ASK AUTHOR]).

## Accepted risks (author instruction, chat 2026-09-30: mentor draft, proceed with defaults)
- All checkpoint defaults Q-001..Q-013 accepted by instruction, not individually reviewed.
- Related work read at abstract/title level only (L019); ~12 bib keys of main.tex not carried.
- Steps 1-2 and 8-9 run in the same context as drafting (isolation: none); G2 has no tool and is recorded as unverified.

## Assumed venue rules
- IEEE conference, IEEEtran conference class, 8 pages including references assumed; no official call consulted.

## Claims awaiting confirmation (writer-derived in revision v002)
- C070-C076 (training data, calibrator split, constant scoring under lesion agreement, match-rate definition, lesion detector per site, VLM prompt, constant fitting set) -- drawn from run summaries, pre-registration and code, not stated in the author's manuscript.
- L023-L027 additional caveats.

## Review round v002_1 (second blind review) -- items not closable by wording
- finding:22 / inference:1 -- non-separability rests on point estimates; paired constant-minus-pipeline CIs must be regenerated (same item as the MISSING RESULT above).
- finding:23 -- pre-registration public anchor ([ASK AUTHOR]).
- finding:29 / inference:0 -- title generality (author decision; Q-001 kept the author's title).
- inference:11 -- VLM probe rests on one blank, one noise and two real images; a systematic content-free probe across all 164 images is future work; decoding settings [ASK AUTHOR].
- inference:12 -- hash check of the lesion detector's DENTEX training images against the 164 scored images is not recorded ([ASK AUTHOR]).
