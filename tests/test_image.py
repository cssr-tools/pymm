"""Test the image mode functionality"""

import os
import pathlib
from pymm.core.pymm import main

dirname: pathlib.Path = pathlib.Path(__file__).parent


def test_image():
    """See configs/parameters.txt"""
    os.chdir(f"{dirname}/configs")
    main()
    assert os.path.exists("./output/mesh.msh")
