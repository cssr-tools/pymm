# SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0

"""Test the device mode functionality"""

import os
import pathlib
import subprocess

testpth: pathlib.Path = pathlib.Path(__file__).parent


def test_device():
    """See configs/whiteish_grains.toml"""
    if not os.path.exists(f"{testpth}/output"):
        os.system(f"mkdir {testpth}/output")
    subprocess.run(
        [
            "pymm",
            "-i",
            f"{testpth}/configs/whiteish_grains.png",
            "-p",
            f"{testpth}/configs/whiteish_grains.toml",
            "-g",
            "gmsh",
            "-t",
            "all",
            "-m",
            "device",
            "-o",
            f"{testpth}/output/files",
        ],
        check=True,
    )
    assert os.path.exists(
        f"{testpth}/output/files/VTK_tracerTransport/tracerTransport_3.vtk"
    )
