# SPDX-FileCopyrightText: 2022-2025 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0
# pylint: disable=R0912,R0915,E1102

"""Main script for pymm"""

import os
import glob
import argparse
import tomllib
import sys
import numpy as np
import porespy as ps
import skimage.transform
import matplotlib as mpl
import matplotlib.pyplot as plt
from alive_progress import alive_bar
from skimage import io, measure
from mako.template import Template


def pymm():
    """Python for microsystems"""
    parser = argparse.ArgumentParser(
        description="Main script to run the workflow on a microsystem configuration."
    )
    parser.add_argument(
        "-i",
        "--image",
        default="microsystem.png",
        help="The base name of the image ('microsystem.png' by default).",
    )
    parser.add_argument(
        "-p",
        "--parameters",
        default="parameters.toml",
        help="The base name of the parameter file ('parameters.toml' by default).",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default="image",
        help="The configuration of the microsystem, currently only image and device"
        "supported ('image' by default).",
    )
    parser.add_argument(
        "-t",
        "--type",
        default="mesh",
        help="Run the whole framework ('all'), only the generation of the PNG figures "
        "with the segmentation to grains, voids, and boundary ('pngs'), the mesh files "
        "for Gmsh ('mesh'), keep the current mesh and only simulate the flow velocity "
        "field ('flow'), mesh and flow ('mesh_flow'), flow and tracer ('flow_tracer'), "
        "or only tracer simulations ('tracer') ('mesh' by default).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="The base name of the output folder ('output' by default).",
    )
    parser.add_argument(
        "-g",
        "--gmsh",
        default="gmsh",
        help="The full path to the gmsh executable or simple Gmsh if it runs from the "
        "terminal ('gmsh' by default).",
    )
    cmdargs = vars(parser.parse_known_args()[0])
    dic = {"fol": os.path.abspath(cmdargs["output"].strip())}  # Name for output folder
    dic["gmsh_path"] = cmdargs["gmsh"]  # Command to execute gmsh
    dic["wtr"] = cmdargs["type"]  # Parts of the workflow to run
    dic["mode"] = cmdargs["mode"]  # Configuration of the microsystem
    dic["pat"] = os.path.dirname(__file__)[:-5]  # Path to the pyff folder
    # Read the input values
    if not os.path.exists(cmdargs["parameters"]):
        print(f"The file {cmdargs['parameters']} is not found.")
        sys.exit()
    if cmdargs["parameters"].split(".")[-1] == "txt":
        print("toml is used now for the parameter file; please update the file.")
        sys.exit()
    with open(cmdargs["parameters"], "rb") as file:
        dic.update(tomllib.load(file))
    print("\nExecuting pymm, please wait.")
    if dic["wtr"] in ["all", "pngs", "mesh", "mesh_flow"]:
        # Generate the image
        process_image(dic, cmdargs["image"])
        # Extract the coordinates of the image borders
        extract_borders(dic)
        if dic["wtr"] in ["all", "mesh", "mesh_flow"]:
            if dic["inletLocation"].lower() == "left":
                dic["inlet"], dic["outlet"] = "L", "R"
            elif dic["inletLocation"].lower() == "top":
                dic["inlet"], dic["outlet"] = "T", "B"
            elif dic["inletLocation"].lower() == "right":
                dic["inlet"], dic["outlet"] = "R", "L"
            elif dic["inletLocation"].lower() == "bottom":
                dic["inlet"], dic["outlet"] = "B", "T"
            else:
                print(f"Invalid inletLocation {dic['inletLocation']}.")
                sys.exit()
            # Identify the points on the borders
            identify_cells(dic)
            # Set the boundary tags
            boundary_tags_left_bottom(dic)
            boundary_tags_right_top(dic)
            # Write the .geo file
            write_geo(dic)
    if dic["wtr"] in ["all", "mesh_flow", "flow", "flow_tracer"]:
        # Set up of the files for the Flow simulations and run them
        if not os.path.exists(f"{dic['fol']}/mesh.msh"):
            print("Run first either -t all or -t mesh.")
            sys.exit()
        run_stokes(dic)
    if dic["wtr"] in ["all", "flow_tracer", "tracer"]:
        if not os.path.exists(f"{dic['fol']}/OpenFOAM/flowStokes"):
            print("Run first either -t all or -t mesh_flow.")
            sys.exit()
        # Set up of the files for the Tracer simulations and run them
        run_tracer(dic)
    print(
        "\nThe execution of pymm succeeded. "
        + f"The generated files have been written to {dic['fol']}\n"
    )


def process_image(dic, in_image):
    """
    Function to process the input image

    Args:
        dic (dict): Global dictionary with required parameters
        in_image (str): Name of the input image data

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    # Read the image
    im0 = np.array(io.imread(in_image, as_gray=True))
    # Convert the image to binary (black and white) and rescale
    dic["im"] = []
    meaning = 1 - 2 * dic["grainMeaning"]
    for i in range(im0.shape[0]):
        imbr = []
        for j in range(im0.shape[1]):
            if i == 0 or i == im0.shape[0] - 1 or j == 0 or j == im0.shape[1] - 1:
                imbr.append(True)
            elif (i in (1, im0.shape[0] - 2)) and dic["mode"] == "device":
                imbr.append(False)
            elif meaning * im0[im0.shape[0] - 1 - i][j] < meaning * dic["threshold"]:
                imbr.append(False)
            else:
                imbr.append(True)
        dic["im"].append(imbr)
    dic["im"] = np.array(dic["im"])
    dic["im"] = skimage.transform.rescale(dic["im"], dic["rescale"])
    dic["imH"], dic["imL"] = dic["im"].shape[0], dic["im"].shape[1]

    # Add arbitrary border to extract the image boundaries
    dic["ad_bord"] = 50
    dic["im"] = np.pad(dic["im"], dic["ad_bord"], pad_with, padder=1)

    # Save the binary image for visualization
    if not os.path.exists(f"{dic['fol']}"):
        os.system(f"mkdir {dic['fol']}")
    fig, axis = plt.subplots()
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray_r"],
    )
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['fol']}/binary_image.png", dpi=600)
    # Extract the contour of the grains on the image border and interior
    dic["border"] = ps.filters.trim_small_clusters(
        dic["im"], size=(dic["imH"] + 2 * dic["imL"]) * dic["ad_bord"]
    )
    dic["cn_border"] = measure.find_contours(
        dic["border"], 0.5, fully_connected="high", positive_orientation="high"
    )
    grains = ps.filters.trim_small_clusters(
        np.logical_and(np.bitwise_not(dic["border"]), dic["im"]),
        size=dic["grainsSize"],
    )
    grains = grains[dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]]
    dic["cn_grains"] = measure.find_contours(
        grains, 0.5, fully_connected="high", positive_orientation="high"
    )
    make_figures(dic)


def make_figures(dic):
    """
    Function to make figures with the extract grains and contours

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    # Save the extracted border for visualization
    fig, axis = plt.subplots()
    axis.imshow(
        dic["border"][
            dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]
        ],
        cmap=mpl.colormaps["gray_r"],
    )
    lmax = 0
    for contour in dic["cn_border"]:
        contour = measure.approximate_polygon(contour, tolerance=dic["borderTol"])
        peri = max(
            (contour[:, 0] - np.roll(contour[:, 0], 1)) ** 2
            + (contour[:, 1] - np.roll(contour[:, 1], 1)) ** 2
        )
        if peri > lmax:
            lmax = peri
            dic["bnd"] = contour
    axis.plot(
        dic["bnd"][:, 1] - dic["ad_bord"],
        dic["bnd"][:, 0] - dic["ad_bord"],
        linewidth=dic["lineWidth"],
    )
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['fol']}/extracted_border.png", dpi=600)

    # Save the interior grains
    fig, axis = plt.subplots()
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray_r"],
    )
    lmax = 0
    for contour in dic["cn_grains"]:
        bng = measure.approximate_polygon(contour, tolerance=dic["grainsTol"])
        if len(contour) > 3:
            axis.plot(bng[:, 1], bng[:, 0], linewidth=dic["lineWidth"])
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['fol']}/interior_grains.png", dpi=600)

    # Save the extracted border + interior grains
    fig, axis = plt.subplots()
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray_r"],
    )
    axis.plot(
        dic["bnd"][:, 1] - dic["ad_bord"],
        dic["bnd"][:, 0] - dic["ad_bord"],
        linewidth=dic["lineWidth"],
    )
    lmax = 0
    for contour in dic["cn_grains"]:
        bng = measure.approximate_polygon(contour, tolerance=dic["grainsTol"])
        if len(contour) > 3:
            axis.plot(bng[:, 1], bng[:, 0], linewidth=dic["lineWidth"])
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['fol']}/interior_grains_border.png", dpi=600)


def extract_borders(dic):
    """
    Function to extract the borders of the image

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["pl"], dic["pb"], dic["pr"], dic["pt"] = [], [], [], []
    dic["aa"], dic["dd"], dic["cc"] = 0, 0, 0
    dic["bb"] = min(dic["bnd"][:, 0])
    dic["bl"] = min(dic["bnd"][:, 1])
    dic["bt"] = max(dic["bnd"][:, 0])
    dic["br"] = max(dic["bnd"][:, 1])
    for i in range(len(dic["bnd"]) - 1):
        if dic["bnd"][-i - 1, 0] > dic["bb"] + 1 and dic["aa"] == 0:
            dic["pr"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["bnd"][-i - 1, 0] - dic["ad_bord"],
                ]
            )
        else:
            dic["aa"] = 1
        if (dic["bnd"][-i - 1, 1] > dic["bl"] + 1 and dic["aa"] == 1) and len(
            dic["pl"]
        ) == 0:
            dic["pb"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["bnd"][-i - 1, 0] - dic["ad_bord"],
                ]
            )
        if dic["bnd"][-i - 1, 1] < dic["bl"] + 1:
            dic["dd"] = 1
        if (dic["bnd"][-i - 1, 0] > dic["bb"] - 1 and dic["dd"] == 1) and (
            dic["cc"] == 0 and len(dic["pb"]) > 0
        ):
            dic["pl"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["bnd"][-i - 1, 0] - dic["ad_bord"],
                ]
            )
        if dic["bnd"][-i - 1, 0] > dic["bt"] - 1 and dic["aa"] == 1:
            dic["cc"] = 1
        if len(dic["pl"]) > 0 + 1 and dic["cc"] == 1:
            dic["pt"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["bnd"][-i - 1, 0] - dic["ad_bord"],
                ]
            )


def pad_with(vector, pad_width, _iaxis, kwargs):
    """
    Function to add extra border to later extract the image boundaries
    see https://numpy.org/doc/stable/reference/generated/numpy.pad.html
    """
    pad_value = kwargs.get("padder", 10)
    vector[: pad_width[0]] = pad_value
    vector[-pad_width[1] :] = pad_value


def identify_cells(dic):
    """
    Function to extract the cell locations on the borders

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["point"] = []
    for i in range(len(dic["pl"])):
        dic["point"].append([dic["pl"][i][0], dic["pl"][i][1]])
    for i in range(len(dic["pt"]) - 1):
        dic["point"].append([dic["pt"][i + 1][0], dic["pt"][i + 1][1]])
    for i in range(len(dic["pr"])):
        dic["point"].append([dic["pr"][i][0], dic["pr"][i][1]])
    for i in range(len(dic["pb"])):
        dic["point"].append([dic["pb"][i][0], dic["pb"][i][1]])
    dic["point"].append(dic["point"][0])


def boundary_tags_left_bottom(dic):
    """
    Function to identify the wall, left, and bottom boundary tags

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["bdnL"], dic["bdnT"], dic["wall"] = [], [], []
    dic["j"] = 0
    for _ in range(len(dic["pl"]) - 1):
        if (
            abs(dic["bl"] - dic["ad_bord"] - dic["point"][dic["j"]][0]) < 1
            and abs(dic["bl"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][0]) < 1
        ):
            dic["bdnL"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1
    for _ in range(len(dic["pt"])):
        if (
            abs(dic["bt"] - dic["ad_bord"] - dic["point"][dic["j"]][1]) < 1
            and abs(dic["bt"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][1]) < 1
        ):
            dic["bdnT"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1


def boundary_tags_right_top(dic):
    """
    Function to identify the wall, right, and top boundary tags

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["bdnR"], dic["bdnB"] = [], []
    for _ in range(len(dic["pr"])):
        if (
            abs(dic["br"] - dic["ad_bord"] - dic["point"][dic["j"]][0]) < 1
            and abs(dic["br"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][0]) < 1
        ):
            dic["bdnR"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1
    if len(dic["pb"]) == 0:
        dic["bdnB"].append(dic["j"])
    else:
        for _ in range(len(dic["pb"])):
            if (
                abs(dic["bb"] - dic["ad_bord"] - dic["point"][dic["j"]][1]) < 1
                and abs(dic["bb"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][1]) < 1
            ):
                dic["bdnB"].append(dic["j"])
            else:
                dic["wall"].append(dic["j"])
            dic["j"] += 1


def write_geo(dic):
    """
    Function to write the Gmsh .geo file

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    mytemplate = Template(filename=f"{dic['pat']}/templates/grid/{dic['mode']}.mako")
    var = {"dic": dic}
    dic["geo"] = mytemplate.render(**var).split("\n")
    tmp, nog = "", 0
    for i, row in enumerate(dic["geo"]):
        if row[:5] == "Plane":
            nol = i
            break
    with alive_bar(len(dic["cn_grains"])) as bar_animation:
        for contour in dic["cn_grains"]:
            bar_animation()
            contour = measure.approximate_polygon(contour, tolerance=dic["grainsTol"])
            points = []
            if len(contour) > 3:
                for i in range(len(contour) - 1):
                    points.append([contour[i, 1], contour[i, 0]])
            if len(points) > 0:
                nog += 1
                tmp += f'Tp[] = Point "*";\nh({nog}) = hs\n;'
                for i, point in enumerate(points):
                    tmp += f"Point(#Tp[]+{i+1}) = {{(rL/L)*{point[0]}, "
                    tmp += f"{point[1]}*rH/H, 0, h({nog})}};\n"
                tmp += 'Tp1[] = Point "*";\nFor i In {#Tp[]+1 : #Tp1[] - 1}\n'
                tmp += (
                    "  Line(i)={i, i + 1};\nEndFor\nLine(#Tp1[])={#Tp1[], #Tp[]+1};\n"
                )
                tmp += "Line Loop(1+n+1)={#Tp[]+1: #Tp1[]};\nn = n+1;\n"
    dic["geo"] = dic["geo"][:nol] + tmp.split("\n") + dic["geo"][nol:]
    with open(f"{dic['fol']}/mesh.geo", "w", encoding="utf8") as file:
        file.write("\n".join(dic["geo"]))
    os.system(f"{dic['gmsh_path']} {dic['fol']}/mesh.geo -3 & wait")


def run_stokes(dic):
    """
    Function to write the openFOAM files to run the Navier-Stokes flow simulations

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    var = {"dic": dic}
    if not os.path.exists(f"{dic['fol']}/OpenFOAM"):
        os.system(f"mkdir {dic['fol']}/OpenFOAM")
    for name in ["OpenFOAM/flowStokes", "VTK_flowStokes"]:
        if os.path.exists(f"{dic['fol']}/{name}"):
            os.system(f"rm -rf {dic['fol']}/{name}")
        os.system(f"mkdir {dic['fol']}/{name}")
    for name in ["0", "constant", "system"]:
        os.system(f"mkdir {dic['fol']}/OpenFOAM/flowStokes/{name}")
    for file in [
        "0/p",
        "0/U",
        "constant/physicalProperties",
        "constant/momentumTransport",
        "system/controlDict",
        "system/fvSchemes",
        "system/fvSolution",
    ]:
        mytemplate = Template(
            filename=f"{dic['pat']}/templates/OpenFOAM/flowStokes/{file}.mako"
        )
        filled_template = mytemplate.render(**var)
        with open(
            f"{dic['fol']}/OpenFOAM/flowStokes/{file}",
            "w",
            encoding="utf8",
        ) as file:
            file.write(filled_template)
    os.system(f"cp {dic['fol']}/mesh.msh {dic['fol']}/OpenFOAM/flowStokes")
    os.chdir(f"{dic['fol']}/OpenFOAM/flowStokes")
    os.system("gmshToFoam mesh.msh & wait")

    with open("constant/polyMesh/boundary", "r", encoding="utf8") as file:
        dic["boundary"] = file.readlines()
        dic["boundary"][20] = "type      empty;"
    mytemplate = Template(filename=f"{dic['pat']}/templates/utils/boundary.mako")
    var = {"dic": dic}
    filled_template = mytemplate.render(**var)
    with open("constant/polyMesh/boundary", "w", encoding="utf8") as file:
        file.write(filled_template)

    # Running the steady-state flow simulation
    os.system("foamRun -solver incompressibleFluid & wait")
    os.system("foamToVTK & wait")
    os.system(f"cp -r VTK/* {dic['fol']}/VTK_flowStokes")


def run_tracer(dic):
    """
    Function to write the openFOAM files to run the Tracer flow simulations

    Args:
        dic (dict): Global dictionary with required parameters
    """
    for name in ["VTK_tracerTransport", "OpenFOAM/tracerTransport"]:
        if os.path.exists(f"{dic['fol']}/{name}"):
            os.system(f"rm -rf {dic['fol']}/{name}")
        os.system(f"mkdir {dic['fol']}/{name}")
    for name in ["0", "constant", "system"]:
        os.system(f"mkdir {dic['fol']}/OpenFOAM/tracerTransport/{name}")
    var = {"dic": dic}
    for file in [
        "0/T",
        "constant/physicalProperties",
        "constant/momentumTransport",
        "constant/fvConstraints",
        "system/controlDict",
        "system/topoSetDict",
        "system/fvSchemes",
        "system/fvSolution",
    ]:
        mytemplate = Template(
            filename=f"{dic['pat']}/templates/OpenFOAM/tracerTransport/{file}.mako"
        )
        filled_template = mytemplate.render(**var)
        with open(
            f"{dic['fol']}/OpenFOAM/tracerTransport/{file}",
            "w",
            encoding="utf8",
        ) as file:
            file.write(filled_template)
    os.chdir(f"{dic['fol']}/OpenFOAM/flowStokes")
    list_of_folders = glob.glob(f"{dic['fol']}/OpenFOAM/flowStokes/*/")
    list_of_folders.remove(max(list_of_folders, key=os.path.getctime))
    latest_folder = max(list_of_folders, key=os.path.getctime)
    os.system(f"cp {latest_folder}U {dic['fol']}/OpenFOAM/tracerTransport/0/")
    os.system(f"cp {latest_folder}p {dic['fol']}/OpenFOAM/tracerTransport/0/")
    os.system(
        f"cp -r {dic['fol']}/OpenFOAM/flowStokes/constant/polyMesh "
        f"{dic['fol']}/OpenFOAM/tracerTransport/constant/"
    )
    os.chdir(f"{dic['fol']}/OpenFOAM/tracerTransport")
    os.system("topoSet & wait")

    # Running the simulation of tracer transport
    os.system("foamRun & wait")
    os.system("foamToVTK & wait")
    os.system(f"cp -r VTK/* {dic['fol']}/VTK_tracerTransport")


def main():
    """Main function"""
    pymm()


# {
# Copyright 2022-2025, NORCE Research AS, Computational
# Geosciences and Modelling.

# This file is part of the pymm module.

# pymm is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pymm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.
# }
