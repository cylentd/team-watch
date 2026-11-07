"""Capture deterministic Chapter 5 holds (the power riser) using the existing shared static server."""
from constants_capture import PLAY_READY_TIMEOUT_MS

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


URL = 'http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/?film'
SIZES = [(360, 800), (390, 844), (1440, 900), (1920, 1080)]
TIMES = [77.9, 78.3, 79.5, 80.2, 82.2, 83, 84.2, 85, 86.2, 87, 88.2, 89, 90.2, 91, 92.2, 93.5, 94.8, 96.3, 97.8]


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
