"""Test the device mode functionality"""

import os
import pathlib
import subprocess

dirname: pathlib.Path = pathlib.Path(__file__).parent


def test_device():
    """See configs/parameters.txt"""
    os.chdir(f"{dirname}/configs")
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
    assert os.path.exists("./files/mesh.msh")
