import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def built():
    """Generuje wszystkie strony (render_all) raz na sesje i zwraca korzen repo."""
    from build_pages import render_all

    render_all(REPO_ROOT)
    return REPO_ROOT
