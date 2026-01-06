import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def repo_fixture(tmp_path: Path):
    def _load(*parts: str) -> Path:
        fixture_dir = Path(__file__).parent / "fixtures"
        source = fixture_dir.joinpath(*parts)
        if not source.exists():
            raise FileNotFoundError(f"Fixture not found: {source}")
        shutil.copytree(source, tmp_path, dirs_exist_ok=True)
        return tmp_path

    return _load
