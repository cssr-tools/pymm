"""Test the device mode functionality"""

import os
import subprocess


def test_device():
    """See configs/parameters.txt"""
    cwd = os.getcwd()
    os.chdir(f"{os.getcwd()}/tests/configs")
    subprocess.run(
        [
            "pymm",
            "-i",
            "microsystem.png",
            "-p",
            "parameters.txt",
            "-g",
            "gmsh",
            "-t",
            "mesh",
            "-m",
            "device",
            "-o",
            "files",
        ],
        check=True,
    )
    assert os.path.exists("./files/mesh.geo")
    os.chdir(cwd)
