"""Chapter 1's words come from the edition's draft block: each beat's headline reads the real numbers,
and a draft block missing a field the film reads is refused where it enters."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'
SOURCE = ROOT / 'draft-data.mjs'
EDITION = ROOT / 'edition.json'


def run(expression, draft=None):
    draft = draft if draft is not None else json.loads(EDITION.read_text(encoding='utf-8'))['draft']
    script = (f'import * as data from {json.dumps(SOURCE.as_uri())};'
              f'const draft = {json.dumps(draft)};'
              f'try {{ console.log(JSON.stringify({{ok: {expression}}})); }}'
              f'catch (error) {{ console.log(JSON.stringify({{error: error.message}})); }}')
    result = subprocess.run(['node', '--input-type=module'], input=script,   # stdin: the board is too long for a command line
                            text=True, capture_output=True, check=True, encoding='utf-8')
    return json.loads(result.stdout)


def test_every_headline_reads_the_seasons_real_numbers():
    words = run('data.receipts(data.checkDraft(draft))')['ok']
    assert {beat: entry['headline'] for beat, entry in words.items()} == {
        'board': 'Draft spot vs. reality.',
        'steal': 'An eighth-round bargain.',
        'traded': 'New team. Same disappointment.',
        'sleeper': 'Eighth-round rock.',
        'curse': 'The Godwin Curse',
        'injury': 'Season cut short.',
        'finale': 'Romo’s value ran deep.',
    }


def test_the_sublines_answer_the_headline_without_naming_the_player_on_the_card():
    words = run('data.receipts(draft)')['ok']
    assert words['steal']['sub'] == 'Four top-12 weeks. No busts.'
    assert words['traded']['sub'] == 'Two starts. No top-36 finishes.'
    assert words['sleeper']['sub'] == 'Top-12 back in 6 of 7.'
    assert words['curse']['sub'] == 'COOKed tempted fate.'
    assert words['injury']['sub'] == '3 games from a second-rounder.'   # ch17: numerals, rule 25
    # The finale's list and total carry it: no subline (David, 2026-11-04).
    assert words['finale']['sub'] == ''


def test_a_pad_says_one_big_word_for_its_place():
    # Revision 8: the bench folds into the team's roster stop (David, 2026-11-04).
    assert run("data.stationText({kind: 'roster', team: 3})")['ok'] == 'ROSTER'
    assert run("data.stationText({kind: 'pit', team: 2})")['ok'] == 'WAIVER'


@pytest.mark.parametrize('name,card', [('Chuba Hubbard', 'C. Hubbard'), ('Matthew Golden', 'M. Golden'),
                                       ('A.J. Brown', 'A.J. Brown'), ('Chris Godwin Jr.', 'C. Godwin'),
                                       ('Amon-Ra St. Brown', 'A. St. Brown'), ('Rams', 'Rams')])
def test_a_card_names_the_player_by_first_initial_and_surname(name, card):
    assert run(f'data.cardName({json.dumps(name)})')['ok'] == card


@pytest.mark.parametrize('field', ['picks', 'teams', 'through'])
def test_a_draft_block_missing_a_field_is_refused(field):
    draft = json.loads(EDITION.read_text(encoding='utf-8'))['draft']
    del draft[field]
    assert 'Invalid draft block' in run('data.checkDraft(draft)', draft)['error']


def test_a_featured_pick_that_is_not_on_the_board_is_refused():
    draft = json.loads(EDITION.read_text(encoding='utf-8'))['draft']
    draft['beats']['curse']['overall'] = 999
    assert run('data.checkDraft(draft)', draft)['error'] == 'Invalid draft block: curse'
