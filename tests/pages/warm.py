"""Open a module's shared component contexts before its first test (2026-10-06).

`mount` (tests/component.py) keeps one browser context per (surface, size, init) a module asks for, and the first
`mount` of each key pays for the context and the cold first load. That cost belongs to the module's shared state,
not to whichever test happens to run first, so a module fixture opens its keys once:

    @pytest.fixture(scope="module")
    def mount(base_mount):
        return warm(base_mount, ("roster", PHONE), ("roster", (390, 844), (MOTION,)))

(with `from component import mount as base_mount`). Every test still mounts, and so reloads, its own page.
Since 2026-10-06 `mount` opens the keys its tests name in literals by itself (`component.module_keys`), so this
is a pass-through to `Mounter.prepare`, which skips a key already open: it still covers a key a test reaches
through a helper.
"""


def warm(mount, *keys):
    """Open each `(surface, size[, init])` once, so the module's contexts exist; returns `mount`."""
    for surface, size, *rest in keys:
        mount.prepare(surface, size=size, init=tuple(rest[0]) if rest else ())
    return mount
