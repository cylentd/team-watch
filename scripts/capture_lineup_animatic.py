"""Capture deterministic Chapter 4 holds using the existing shared static server."""
from constants_capture import PLAY_READY_TIMEOUT_MS

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


URL = 'http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/?film'
SIZES = [(360, 800), (390, 844), (1440, 900), (1920, 1080)]
TIMES = [61.9, 62.2, 63.6, 64.3, 65.6, 66.4, 67.5, 69.4, 70.2, 71.9, 73.6, 74.3, 75.9, 77.5, 78.3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in SIZES:
                context = browser.new_context(viewport={'width': width, 'height': height})
                try:
                    page = context.new_page()
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(URL)
                    expect(page.locator('[data-play]')).to_be_enabled(timeout=PLAY_READY_TIMEOUT_MS)
                    for time in TIMES:
                        page.locator('[data-seek]').evaluate('(node,time)=>{node.value=time;node.dispatchEvent(new Event("input",{bubbles:true}));}', time)
                        page.screenshot(path=str(args.output / f'{width}x{height}-{time}.png'))
                finally:
                    context.close()
        finally:
            browser.close()
    print(json.dumps({'frames': len(SIZES) * len(TIMES), 'errors': errors, 'output': str(args.output)}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
