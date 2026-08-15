# 2026-08-15 — Strategic re-plan after the 2026 foundation-model literature scan

**Session goal:** Re-derive the project's publication strategy against the August 2026 state of the
literature — in particular DentFound — and produce a costed, week-by-week plan that lands a
submittable research paper by the 14 October project deadline.

## What was done

- **Reconciled local work with the upstream repo restructure.** Local `main` was 6 commits behind
  and carried ~880 lines of uncommitted LaTeX edits at the pre-restructure path
  `pes_capstone_report/`, which upstream had moved to `docs/reports/pes_capstone_report/`.
  Stashed with `-u`, fast-forwarded to `e5a4419`, popped, resolved a rename/delete conflict on
  `main.pdf` (kept the local deletion — it was a stale build), then manually relocated the
  untracked leftovers: 13 figures into `docs/reports/pes_capstone_report/figures/` and
  `06_cej_estimation_v3.ipynb` into `notebooks/bone_loss/`. Removed the emptied
  `pes_capstone_report/` and `notebooks/Bone Loss/` directories. **Nothing committed** — the
  reconciled changes are staged/untracked and awaiting review.
- **Read the repo cold** — `docs/README.md`, root `README.md`, `model_metrics.md`, the structure of
  `PAPER_MATERIAL.md`, and all four `docs/research/` documents — to establish the pre-existing plan
  before changing it.
- **Verified the open FDI bug spans two files, not one.** `docs/research/*` and the root README
  both flag `configs/dataset_config.yaml`; `src/utils/fdi_converter.py` lines 20–22 carries the
  *same* wrong lower-arch mapping independently (23→43, 24→44, 25–28→45–48, 29–32→31–34 with
  33/34 duplicated). Both need fixing, and the module docstring encodes the error too.
- **Confirmed Tufts ships tooth polygons.** `configs/dataset_config.yaml` references
  `Segmentation/Segmentation/teeth_mask` and `teeth_polygon.json`. This makes an instance-segmentation
  upgrade annotation-free, which is what unblocked architecture change R1 below.
- **Ran a literature scan** on the DentFound paper and repo plus adjacent 2026 work. Full-text of the
  two Nature papers was **not** reachable — `nature.com` redirects through `idp.nature.com` for both
  DentFound and DentVLM regardless of fetch method, and no Apify connector is configured in this
  session. Findings below come from the GitHub repo, arXiv preprints, PMC, and abstracts. **Full
  methods/figures for both Nature papers still need institutional access.**
- **Wrote `docs/research/MASTER_PLAN_2026H2.md`** — the deliverable. Eight-week schedule with weekly
  exit criteria, six costed architecture changes, dataset assignment rules, a ~35 GPU-hour compute
  budget, venue targets with a go/no-go date, and a risk register.

### Key literature findings

| Finding | Consequence |
|---|---|
| **DentFound code + weights are public** (Apache 2.0, [github.com/ahukui/DentFound](https://github.com/ahukui/DentFound)) — CLIP ViT-L/14 → MLP projection → Vicuna-7B, trained on 8×A100 | Turns the paper that threatened us into a free baseline. Its **training data (101k patients) is not released.** |
| DentFound is **instance-guided** — tooth instance masks ground the LLM; their own ablation covers masks / resolution / staged training | Independent justification that our detect→crop→classify structure is the right bet. Motivates R1/R2. |
| **DentVLM** ([*Nat Commun* 2026](https://arxiv.org/abs/2509.23344)) — 110,447 images, 2.46M bilingual VQA pairs, 7 modalities, 36 tasks; beats 13 junior dentists on 21/36 tasks | **Not cited anywhere in our survey draft.** Arguably a bigger threat to the survey's central gap claim than DentFound. No code/weights/data released. |
| **Ningxia multi-center dataset** ([Li et al. 2024](https://github.com/qinxin99/qinxini)) — 6,580 images, 3 hospitals, periodontitis 2,736 / caries 1,277 / impacted 2,567, segmentation + classification labels, free, ethics-approved (KYLL-2021066) | **The pivot.** Free labelled external validation covering both our diseases. Hosted on Baidu Cloud (pw `3et5`). |
| [GPT-4o numbering study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12468776/) (*Diagnostics*, Sep 2025) — VLMs good on radiopaque findings, poor on radiolucent (caries, periapical lesions) | The hypothesis behind the specialist-vs-foundation comparison, and reason to think a small model can win on our exact tasks. |
| [Large AI Models in Dental Healthcare](https://arxiv.org/html/2606.02914v1) (arXiv, Jun 2026, 97 studies, PRISMA-ScR) and [Vision Foundation Models for Oral & Maxillofacial Radiology](https://arxiv.org/pdf/2510.14532) (Oct 2026) | Two more recent surveys. Adjacent, not subsuming — but must be cited and scoped against explicitly. |

## Decisions made

1. **Ningxia replaces the private clinic dataset as the primary external validation.** The clinic
   track needs IRB approval plus 40–60 hours of dentist annotation; `clinical_dataset_plan.md` §7
   budgets 12–14 weeks for it and names dentist availability as the top risk. We have 8 weeks.
   Ningxia produces *labelled* cross-institution numbers by week 4 instead of label-free shift
   diagnostics by week 10. The clinic track continues in the background (IRB started now, zero
   critical-path cost) and becomes the follow-up paper or a revision-stage strengthener.
   **This is the decision the rest of the plan hangs on.**
2. **The paper's lead claim becomes specialist-vs-foundation-model**, not "we externally validated."
   DentFound's weight release makes the comparison possible and free; nobody has run it on subtle
   radiolucent pathology. Both outcomes are publishable, which de-risks the headline result — a rare
   property worth taking.
3. **Ningxia is locked as test data and will not be trained on.** External validation is the
   single most-cited missing element in this subfield; trading it for a marginal accuracy gain is a
   bad deal. An optional center-wise domain-adaptation experiment is allowed *only* after the frozen
   external number exists.
4. **The Ningxia evaluation is defined as three separate honest measurements, not one.** Ningxia has
   image-level labels + lesion masks; our pipeline emits per-tooth FDI-keyed findings. These do not
   match one-to-one. Rather than paper over it: (a) image-level disease presence — the headline
   external number, and the granularity that is directly comparable to DentFound's output;
   (b) lesion-localisation agreement — which doubles as the quantified XAI metric (T1.5);
   (c) label-free detection/numbering sanity checks. Per-tooth external metrics remain available
   only from clinic data. **Stated as a limitation in the paper, deliberately.**
5. **Upgrade detection to YOLOv11l-seg (R1).** Justified by DentFound's instance-guided ablation,
   costs one ~6h retrain, and needs no new annotation because Tufts already ships polygons. Enables
   mask-aware cropping (R2), which becomes a fourth ablation cell nobody in the retrieved literature
   has reported.
6. **Defer the learned CEJ keypoint head (T2.1 / R7).** It needs CEJ/crest/apex annotations we do
   not have. Deriving pseudo-labels from Ningxia's periodontitis masks would produce an
   unfalsifiable result, so it is explicitly ruled out rather than left as a tempting option.
   The classical CEJ attempt is reported as a clean negative result instead.
7. **Do not LoRA-fine-tune DentFound.** Technically feasible on our H100 budget, but it would make
   DentFound a component rather than a baseline and destroy the comparison that carries the paper.
8. **Target ISBI 2027 (deadline 26 Oct) with a 30 September go/no-go**, falling back to
   *Oral Radiology* (free under subscription, in scope, no deadline). The 4-page limit is treated as
   a feature — it forces the paper down to the two strongest contributions.
9. **Survey central claim reframed** to survive both VLMs: *no openly reproducible system — open in
   both weights and training data — integrates caries detection, severity staging, bone-loss
   quantification and explainability in a single panoramic pipeline.* DentFound releases weights but
   not data; DentVLM releases neither. Verifiable, and our research paper then fills the gap the
   survey names.

## Open questions

1. **Can the Ningxia dataset actually be downloaded from India?** It is on Baidu Cloud, which
   commonly throttles international transfers and may require the desktop client or an account.
   **This is week-1 critical path and it fails slowly rather than loudly.** Fallbacks, in order:
   email the maintainer (`qinxinni99@gmail.com`, offered in the repo for technical issues); then
   vzrad2 / the children's panoramic dataset as a weaker but non-blocking substitute.
2. **Full text of DentFound and DentVLM is unread.** Both Nature URLs redirect to an auth gate.
   Needs PES institutional access. Specifically unknown: DentFound's exact caries/periodontal
   sub-task metrics (needed to make the C1 comparison table fair), and its per-disease breakdown.
3. **Will DentFound actually run?** Linux-only, `flash-attn`, Vicuna-7B + CLIP from HF. Budgeted a
   full week (W5) with environment setup starting in W4, but dependency failure is a live risk to
   contribution C1.
4. **Ningxia caries labels may not be comparable to DENTEX caries labels.** Their annotation protocol
   (ITK-SNAP contour tracing) and disease definition were not verified against DENTEX's. Check before
   reporting a cross-dataset caries number, or the comparison is apples-to-oranges.
5. **Nothing from this session or the previous three is pushed to `origin`.** Carried over from the
   2026-08-13 file and still true. Working tree currently holds staged LaTeX edits, 13 untracked
   figures, `06_cej_estimation_v3.ipynb`, the new master plan, and this file.
6. **The untracked root `survey_paper/` directory is a stale 47-reference draft**, superseded by
   `Survey Paper Latex folder/` (70 refs). Flagged, deliberately left untouched, needs a
   keep-or-archive decision — and per `CLAUDE.md` rule 3 it must be *relocated* to `_repo_archive/`,
   never deleted.
7. **Table IV of the survey is still only ~3/25 rows fact-checked.** Carried over unchanged from
   2026-08-13. Still the biggest academic-integrity risk in the survey.

## Next steps

Ordered. Items 1–3 block everything else; 4–7 are parallel and cheap.

1. **Attempt the Ningxia download today.** Everything in contribution C2 depends on it. See open
   question 1 for the fallback chain.
2. **Fix the Universal→FDI lower-arch mapping** in *both* `configs/dataset_config.yaml`
   (lines 122–131) and `src/utils/fdi_converter.py` (lines 20–22, plus the docstring), and cover it
   in `tests/test_fdi_converter.py`. Every lower-jaw finding is currently mis-numbered.
3. **Close T0.1 — the augmentation audit.** Read the caries training code, establish what actually
   ran, choose enable-and-rerun *or* state-it-honestly, and write the decision down with a date.
   Nothing in the research paper is trustworthy until this is resolved.
4. Provision the E2E Networks H100 and verify the Ultralytics + PyTorch environment.
5. Start IRB / ethics paperwork for the clinic data — longest lead time of anything, zero
   critical-path cost.
6. Email the PES library about Read-and-Publish agreements (Springer / Oxford / Elsevier / Wiley).
7. Confirm authorship order and the ISBI-vs-journal decision with Dr. Mamatha H R.

Then W2 begins: canonical detector (T0.6) retrained as YOLOv11l-seg, DENTEX held-out test split
(T0.2), macro-F1 checkpointing across all four classifiers (T0.3), and mask-aware cropping (R2).
Full schedule in [`../research/MASTER_PLAN_2026H2.md`](../research/MASTER_PLAN_2026H2.md) §5.
