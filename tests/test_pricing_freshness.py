"""Advisory test: warn (don't fail) when token pricing rates are >90 days old."""
import datetime
import re
import warnings
from pathlib import Path


_RATE_FILE = Path(__file__).parent.parent / "src" / "actual_cost_calculator.py"
_DATE_RE = re.compile(r"captured (\d{4}-\d{2}-\d{2})")
_STALENESS_DAYS = 90


def test_token_rates_not_stale():
    """Each 'captured YYYY-MM-DD' marker in the rate file is within 90 days.

    This test never FAILS on staleness — it emits warnings via pytest.warns when stale.
    However, it WILL fail if no 'captured YYYY-MM-DD' markers are found at all,
    which indicates the regex or comment format has drifted.
    Run with `-W error` to escalate staleness warnings locally.
    """
    text = _RATE_FILE.read_text()
    matches = list(_DATE_RE.finditer(text))
    assert matches, (
        f"No 'captured YYYY-MM-DD' markers found in {_RATE_FILE}. "
        "The regex or comment format may have drifted; this advisory has gone silent."
    )
    today = datetime.date.today()
    stale = []
    for match in matches:
        captured = datetime.date.fromisoformat(match.group(1))
        if (today - captured).days > _STALENESS_DAYS:
            stale.append(match.group(1))
    if stale:
        warnings.warn(
            f"Token rates older than {_STALENESS_DAYS} days: {stale}. "
            f"Refresh from provider docs.",
            UserWarning,
            stacklevel=2,
        )
