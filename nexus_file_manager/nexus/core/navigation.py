"""Back/forward history + path helpers (mock Windows-style paths; HOOK: swap for pathlib once real)."""
from __future__ import annotations

SEP = "\\"


def split_path(path: str) -> list[str]:
    return [s for s in path.replace("/", SEP).split(SEP) if s]


def join_path(segments: list[str]) -> str:
    p = SEP.join(segments)
    return p + SEP if len(segments) == 1 and p.endswith(":") else p


def parent_path(path: str) -> str:
    segs = split_path(path)
    return join_path(segs[:-1]) if len(segs) > 1 else path


class NavigationHistory:
    def __init__(self, start: str):
        self._stack = [start]
        self._i = 0

    @property
    def current(self) -> str:
        return self._stack[self._i]

    @property
    def can_back(self) -> bool:
        return self._i > 0

    @property
    def can_forward(self) -> bool:
        return self._i < len(self._stack) - 1

    def push(self, path: str) -> bool:
        if path == self.current:
            return False
        del self._stack[self._i + 1:]
        self._stack.append(path)
        self._i += 1
        return True

    def back(self) -> str:
        if self.can_back:
            self._i -= 1
        return self.current

    def forward(self) -> str:
        if self.can_forward:
            self._i += 1
        return self.current
