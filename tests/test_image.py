# SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0

"""Test the image mode functionality"""

import os
import pathlib
from pymm.core.pymm import main

testpth: pathlib.Path = pathlib.Path(__file__).parent


def test_image():
    """See configs/parameters.toml"""
    if not os.path.exists(f"{testpth}/output"):
        os.system(f"mkdir {testpth}/output")
    os.chdir(f"{testpth}/output")
    os.system(f"cp {testpth}/configs/parameters.toml .")
    os.system(f"cp {testpth}/configs/microsystem.png .")
    main()
    assert os.path.exists(f"{testpth}/output/output/mesh.msh")
