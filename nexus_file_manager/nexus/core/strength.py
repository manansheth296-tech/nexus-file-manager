"""Password-strength HINT for the Safe Locker meter. UI-only heuristic (length + character variety),
not a security measure. HOOK: swap for a zxcvbn-style estimator when the vault backend lands."""
from __future__ import annotations

LABELS = ["Too short", "Weak", "Fair", "Good", "Strong"]


def password_strength(pw: str) -> int:
    """-> 0 (empty/too short) .. 4 (strong)"""
    if len(pw) < 6:
        return 0
    classes = sum([any(c.islower() for c in pw), any(c.isupper() for c in pw),
                   any(c.isdigit() for c in pw), any(not c.isalnum() for c in pw)])
    score = (len(pw) >= 8) + (len(pw) >= 12) + (classes >= 3) + (classes == 4 and len(pw) >= 10)
    return max(1, min(4, score))
