import uuid
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
