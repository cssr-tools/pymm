# SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0

"""Test in a single grain"""

from pathlib import Path
import subprocess


def test_single_grain(tmp_path, monkeypatch):
    """See configs/whiteish_grains.toml"""
    repo_root = Path(__file__).parents[1]
    monkeypatch.chdir(tmp_path)
    subprocess.run(
        [
            "pymm",
            "-p",
            f"{repo_root}/tests//configs/single_grain.toml",
            "-i",
            f"{repo_root}/tests/configs/single_grain.png",
            "-t",
            "mesh",
            "-o",
            ".",
            "-m",
            "image",
        ],
        check=True,
    )
    mesh = tmp_path / "mesh.msh"
    assert mesh.is_file()

    with open(mesh, "r", encoding="utf8") as f:
        lines = f.readlines()

    num_elements = int(lines[lines.index("$Elements\n") + 1])
    num_nodes = int(lines[lines.index("$Nodes\n") + 1])
    num_lines = len(lines)

    assert num_lines > 15000
    assert num_nodes > 4000
    assert num_elements > 10000
    subprocess.run(
        [
            "pymm",
            "-i",
            f"{repo_root}/tests/configs/single_grain.png",
            "-p",
            f"{repo_root}/tests//configs/single_grain.toml",
            "-t",
            "flow_tracer",
            "-m",
            "image",
            "-o",
            ".",
        ],
        check=True,
    )
    last_vtk = tmp_path / "VTK_tracerTransport" / "tracerTransport_3.vtk"
    assert last_vtk.is_file()
    assert last_vtk.stat().st_size > 0
