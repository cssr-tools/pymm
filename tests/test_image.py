# SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0

"""Test the image mode functionality"""

from pathlib import Path
import shutil
from pymm.core.pymm import main


def test_image(tmp_path, monkeypatch):
    """See configs/parameters.toml"""
    repo_root = Path(__file__).parents[1]
    monkeypatch.chdir(tmp_path)
    input_config = repo_root / "tests" / "configs" / "parameters.toml"
    shutil.copy(input_config, tmp_path / "parameters.toml")
    input_image = repo_root / "tests" / "configs" / "microsystem.png"
    shutil.copy(input_image, tmp_path / "microsystem.png")
    main()
    mesh = tmp_path / "output" / "mesh.msh"
    assert (mesh).is_file()

    with open(mesh, "r", encoding="utf8") as f:
        lines = f.readlines()

    num_lines = len(lines)
    num_nodes = int(lines[lines.index("$Nodes\n") + 1])
    num_elements = int(lines[lines.index("$Elements\n") + 1])

    assert num_lines > 1200000
    assert num_nodes > 300000
    assert num_elements > 900000
