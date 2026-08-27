"""Tests for the C1 few-shot arm.

The one that matters is `test_exemplars_never_touch_the_scored_set`. A few-shot arm that draws
its examples from the evaluation images would post a large, entirely fake gain, and it would look
exactly like a real result. The exemplar pool is restricted to the 86 leakage-excluded images
precisely so that cannot happen, and this pins it.

The message-shape tests exist because an off-by-one between messages and images is silent: the
processor pairs them positionally, so a mismatch shifts every exemplar's answer onto the wrong
radiograph and still runs.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

from c1_vlm_baseline import PROMPT, build_messages, load_exemplars, load_gt  # noqa: E402

DISEASE = Path.home() / "Downloads" / "Capstone" / "DENTEX" / "disease"
needs_data = pytest.mark.skipif(not DISEASE.exists(), reason="DENTEX disease set not on this machine")


@needs_data
def test_exemplars_never_touch_the_scored_set():
    scored = set(load_gt(DISEASE))
    ex = load_exemplars(DISEASE, 8)
    assert ex, "exemplar pool came back empty"
    assert not (set(s for s, _ in ex) & scored)


@needs_data
def test_exemplars_come_from_the_excluded_list():
    import json
    leaked = set(json.loads(
        (REPO_ROOT / "data/dentex/disease_leaked_images.json").read_text())["all_excluded"])
    for stem, _ in load_exemplars(DISEASE, 8):
        assert stem in leaked or f"{stem}.png" in leaked


@needs_data
def test_exemplar_selection_is_deterministic():
    assert load_exemplars(DISEASE, 4) == load_exemplars(DISEASE, 4)


@needs_data
def test_exemplars_carry_caries_codes():
    # A demonstration of "NONE" teaches nothing on a 90.2%-positive set.
    for _, codes in load_exemplars(DISEASE, 4):
        assert codes


@needs_data
def test_more_shots_extends_the_same_prefix():
    """Selection must be a stable prefix, or a 2-shot and 4-shot run share no examples and the
    comparison between them measures two things at once."""
    assert load_exemplars(DISEASE, 4)[:2] == load_exemplars(DISEASE, 2)


def test_zero_shot_message_shape_is_unchanged():
    msgs, images = build_messages(PROMPT, "IMG", [], [])
    assert len(msgs) == 1 and msgs[0]["role"] == "user"
    assert images == ["IMG"]


def test_few_shot_message_and_image_counts_line_up():
    ex = [("a", ["16"]), ("b", ["26", "36"])]
    msgs, images = build_messages(PROMPT, "REAL", ex, ["IA", "IB"])
    assert len(msgs) == 2 * len(ex) + 1
    assert len(images) == len(ex) + 1
    n_image_slots = sum(1 for m in msgs for c in m["content"] if c.get("type") == "image")
    assert n_image_slots == len(images)


def test_few_shot_pairs_each_exemplar_with_its_own_answer():
    ex = [("a", ["16"]), ("b", ["26", "36"])]
    msgs, images = build_messages(PROMPT, "REAL", ex, ["IA", "IB"])
    assert msgs[1]["role"] == "assistant" and msgs[1]["content"][0]["text"] == "16"
    assert msgs[3]["role"] == "assistant" and msgs[3]["content"][0]["text"] == "26, 36"
    assert images[0] == "IA" and images[1] == "IB" and images[-1] == "REAL"


def test_empty_exemplar_answer_is_rendered_as_none():
    msgs, _ = build_messages(PROMPT, "REAL", [("a", [])], ["IA"])
    assert msgs[1]["content"][0]["text"] == "NONE"


def test_real_question_is_always_last():
    ex = [("a", ["16"])]
    msgs, images = build_messages(PROMPT, "REAL", ex, ["IA"])
    assert msgs[-1]["role"] == "user"
    assert images[-1] == "REAL"
