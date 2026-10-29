"""Core password-generation logic.

This module only uses the Python standard library. All randomness comes from
the ``secrets`` module, which pulls from the operating system's
cryptographically secure random number generator.
"""

from __future__ import annotations

import math
import secrets
import string
from typing import List

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
# Quotes, backslash and space are left out on purpose: they cause trouble in
# shells, config files and some login forms.
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/~"
# Characters that are easy to mix up when reading a password aloud or on paper.
AMBIGUOUS = "il1Lo0O"

MIN_LENGTH = 1
MAX_LENGTH = 1024


class PasswordError(ValueError):
    """Raised when the requested password settings are invalid."""


def build_pools(
    lowercase: bool = True,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> List[str]:
    """Return one string of allowed characters per selected character type."""
    pools = []
    if lowercase:
        pools.append(LOWERCASE)
    if uppercase:
        pools.append(UPPERCASE)
    if numbers:
        pools.append(DIGITS)
    if symbols:
        pools.append(SYMBOLS)

    if exclude_ambiguous:
        pools = ["".join(c for c in pool if c not in AMBIGUOUS) for pool in pools]

    return pools


def generate_password(
    length: int = 16,
    *,
    lowercase: bool = True,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> str:
    """Generate one random password.

    The password is guaranteed to contain at least one character from every
    selected character type.

    Raises:
        PasswordError: if the length is invalid, no character type is
            selected, or the length is too short to fit every selected type.
    """
    if isinstance(length, bool) or not isinstance(length, int):
        raise PasswordError("Length must be a whole number.")
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise PasswordError(f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")

    pools = build_pools(lowercase, uppercase, numbers, symbols, exclude_ambiguous)
    if not pools:
        raise PasswordError("Select at least one character type.")
    if length < len(pools):
        raise PasswordError(
            f"Length {length} is too short to include every selected character "
            f"type (need at least {len(pools)})."
        )

    # 1. One guaranteed character from each selected type.
    chars = [secrets.choice(pool) for pool in pools]

    # 2. Fill the remaining slots from the combined pool.
    combined = "".join(pools)
    chars.extend(secrets.choice(combined) for _ in range(length - len(chars)))

    # 3. Shuffle so the guaranteed characters don't sit at predictable positions.
    secrets.SystemRandom().shuffle(chars)

    return "".join(chars)


def estimate_entropy_bits(
    length: int,
    *,
    lowercase: bool = True,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
    exclude_ambiguous: bool = False,
) -> float:
    """Roughly estimate password strength in bits of entropy.

    Computed as ``length * log2(pool size)``. Because every selected type is
    guaranteed to appear, the real figure is very slightly lower; treat this
    as a ballpark number.
    """
    pools = build_pools(lowercase, uppercase, numbers, symbols, exclude_ambiguous)
    pool_size = len("".join(pools))
    if pool_size == 0:
        return 0.0
    return length * math.log2(pool_size)


def describe_strength(bits: float) -> str:
    """Turn an entropy estimate into a plain-English label."""
    if bits < 40:
        return "weak"
    if bits < 60:
        return "fair"
    if bits < 80:
        return "good"
    if bits < 100:
        return "strong"
    return "very strong"
