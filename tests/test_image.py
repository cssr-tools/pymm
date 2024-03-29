"""Test the image mode functionality"""

import os
from pymm.core.pymm import main


def test_image():
    """See configs/parameters.txt"""
    cwd = os.getcwd()
    os.chdir(f"{os.getcwd()}/tests/configs")
    main()
    assert os.path.exists("./output/interior_grains_border.png")
    os.chdir(cwd)
