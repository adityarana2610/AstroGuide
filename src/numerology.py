"""
numerology.py — Chaldean numerology: life path, birth number, and name number.
"""

# ── Chaldean letter → number mapping ─────────────────────────────────────────
# Note: 9 is intentionally absent from the Chaldean system.
_CHALDEAN: dict[str, int] = {}
_MAP = {
    1: "aijqy",
    2: "bkr",
    3: "cgls",
    4: "dmt",
    5: "ehnx",
    6: "uvw",
    7: "oz",
    8: "fp",
}
for _num, _letters in _MAP.items():
    for _ch in _letters:
        _CHALDEAN[_ch] = _num

MASTER_NUMBERS = {11, 22, 33}


def reduce_num(n: int) -> int:
    """Reduce *n* by summing its digits until ≤ 9, preserving master numbers (11, 22, 33)."""
    while n > 9:
        if n in MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def compute_numbers(name: str, date_str: str) -> dict:
    """Compute Chaldean numerology numbers.

    Parameters
    ----------
    name : str
        Full name (only alphabetic characters are used).
    date_str : str
        Date of birth in ``YYYY-MM-DD`` format.

    Returns
    -------
    dict
        ``{life_path: int, birth_number: int, name_number: int}``
    """
    # ── life path ────────────────────────────────────────────────────────
    digit_sum = sum(int(ch) for ch in date_str if ch.isdigit())
    life_path = reduce_num(digit_sum)

    # ── birth number (day of month) ──────────────────────────────────────
    day = int(date_str.split("-")[2])
    birth_number = reduce_num(day)

    # ── name number (Chaldean) ───────────────────────────────────────────
    letter_sum = sum(
        _CHALDEAN.get(ch, 0)
        for ch in name.lower()
        if ch.isalpha()
    )
    name_number = reduce_num(letter_sum)

    return {
        "life_path": life_path,
        "birth_number": birth_number,
        "name_number": name_number,
    }
