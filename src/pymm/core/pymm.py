"""Main script"""

import os
import csv
import glob
import argparse
import numpy as np
import porespy as ps
import skimage.transform
import matplotlib as mpl
import matplotlib.pyplot as plt
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
        default="parameters.txt",
        help="The base name of the parameter file ('parameters.txt' by default).",
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
        help="Run the whole framework ('all'), only the mesh part ('mesh'), "
        "keep the current mesh and only the flow ('flow'), flow and tracer ('flowntracer'), "
        "or only tracer ('tracer') ('mesh' by default).",
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
    dic = {"fol": cmdargs["output"]}  # Name for the output folder
    dic["gmsh_path"] = cmdargs["gmsh"]  # Command to execute gmsh
    dic["wtr"] = cmdargs["type"]  # Parts of the workflow to run
    dic["mode"] = cmdargs["mode"]  # Configuration of the microsystem
    dic["pat"] = os.path.dirname(__file__)[:-5]  # Path to the pyff folder
    dic["cwd"] = os.getcwd()  # Path to the folder of the parameters.txt file
    # Read the input values
    dic = process_input(dic, cmdargs["parameters"])
    if dic["wtr"] in ("all", "mesh"):
        # Generate the image
        dic = process_image(dic, cmdargs["image"])
        # Extract the coordinates of the image borders
        dic = extract_borders(dic)
        # Identify the points on the borders
        dic = identify_cells(dic)
        # Set the boundary tags
        dic = boundary_tags_left_bottom(dic)
        dic = boundary_tags_right_top(dic)
        # Write the .geo file
        dic = write_geo(dic)
    if (dic["wtr"] == "all" or dic["wtr"] == "flow") or dic["wtr"] == "flowntracer":
        # Setting up of the files for the Flow simulations and run it
        dic = run_stokes(dic)
    if (dic["wtr"] == "all" or dic["wtr"] == "flowntracer") or dic["wtr"] == "tracer":
        # Setting up of the files for the Tracer simulations and run it
        run_tracer(dic)


def process_input(dic, in_file):
    """
    Function to process the input file

    Args:

        dic (dict): Global dictionary with required parameters
        in_file (str): Name of the input text file

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    lol = []
    with open(in_file, "r", encoding="utf8") as file:
        for row in csv.reader(file, delimiter="#"):
            lol.append(row)
    dic["Ls"] = float(lol[1][0])  # Length of the microsystem [m]
    dic["Hs"] = float(lol[2][0])  # Heigth of the microsystem [m]
    dic["Ds"] = float(lol[3][0])  # Depth of the microsystem [m]
    dic["thr"] = int(lol[4][0])  # Threshold for converting the image to binary
    dic["res"] = float(lol[5][0])  # rescaled factor for the image
    dic["size_grains"] = int(lol[6][0])  # Minimum size of the grain clusters [pixels]
    dic["tol_border"] = float(
        lol[7][0]
    )  # Tolerance to approximate the border as polygon
    dic["tol_grains"] = float(
        lol[8][0]
    )  # Tolerance to approximate the grains as polygon
    dic["lw"] = float(
        lol[9][0]
    )  # Line width to show the contours in the produced figures
    dic["Cs"] = float(
        lol[10][0]
    )  # Width of the top and bottom channels in the micromodel device [m]
    dic["hz"] = float(lol[11][0])  # Mesh size [m]
    dic["nu"] = float(
        lol[12][0]
    )  # Fluid kinematic viscocity [Dynamic viscocity/fluid_density, m2/s]
    dic["D"] = float(lol[13][0])  # Diffusion coefficient for the tracer [m2/s]
    dic["bc_inlet"] = float(
        lol[14][0]
    )  # Inlet boundary condition (Pressure/fluid_density, [Pa/(kg/m3)])
    dic["t_et"] = float(lol[15][0])  # End time for the tracer simulation [s]
    dic["t_wi"] = float(lol[16][0])  # Time interval to write the tracer results [s]
    dic["p_tol"] = float(lol[17][0])  # Convergence criterium for the pressure solution
    dic["u_tol"] = float(lol[18][0])  # Convergence criterium for the velocity solution
    dic["f_maxI"] = float(
        lol[19][0]
    )  # Maximum number of iterations for the Stokes simulation
    dic["t_dt"] = float(
        lol[20][0]
    )  # Time step in the numerical scheme for the Tracer simulation [s]
    return dic


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
    im0 = np.array(io.imread(in_image))

    # Convert the image to binary (black and white) and rescale
    dic["im"] = []
    for i in range(im0.shape[0]):
        imbr = []
        for j in range(im0.shape[1]):
            if i == 0 or i == im0.shape[0] - 1 or j == 0 or j == im0.shape[1] - 1:
                imbr.append(True)
            elif (i in (1, im0.shape[0] - 2)) and dic["mode"] == "device":
                imbr.append(False)
            elif im0[i][j][2] > dic["thr"]:
                imbr.append(False)
            else:
                imbr.append(True)
        dic["im"].append(imbr)
    dic["im"] = np.array(dic["im"])
    dic["im"] = skimage.transform.rescale(dic["im"], dic["res"])
    dic["imH"] = dic["im"].shape[0]
    dic["imL"] = dic["im"].shape[1]

    # Add arbitrary border to extract the image boundaries
    dic["ad_bord"] = 50
    dic["im"] = np.pad(dic["im"], dic["ad_bord"], pad_with, padder=1)

    # Save the binary image for visualization
    os.system(f"rm -rf {dic['cwd']}/{dic['fol']}")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}")
    fig, axis = plt.subplots(figsize=(4, 4))
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray"],
    )
    fig.savefig(f"{dic['cwd']}/{dic['fol']}/binary_image.png", dpi=600)

    # Extract the contour of the grains on the image border and interior
    dic["border"] = ps.filters.trim_small_clusters(
        dic["im"], size=(dic["imH"] + 2 * dic["imL"]) * dic["ad_bord"]
    )
    dic["cn_border"] = measure.find_contours(
        dic["border"], 0.5, fully_connected="high", positive_orientation="high"
    )
    grains = ps.filters.trim_small_clusters(
        np.logical_and(np.bitwise_not(dic["border"]), dic["im"]),
        size=dic["size_grains"],
    )
    grains = grains[dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]]
    dic["cn_grains"] = measure.find_contours(
        grains, 0.5, fully_connected="high", positive_orientation="high"
    )
    dic = make_figures(dic)
    return dic


def make_figures(dic):
    """
    Function to make figures with the extract grains and contours

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    # Save the extracted border for visualization
    ps.visualization.set_mpl_style()
    fig, axis = plt.subplots()
    axis.imshow(dic["border"], cmap=mpl.colormaps["gray"])
    lmax = 0
    for contour in dic["cn_border"]:
        contour = measure.approximate_polygon(contour, tolerance=dic["tol_border"])
        peri = max(
            (contour[:, 0] - np.roll(contour[:, 0], 1)) ** 2
            + (contour[:, 1] - np.roll(contour[:, 1], 1)) ** 2
        )
        if peri > lmax:
            lmax = peri
            dic["bnd"] = contour
    axis.plot(dic["bnd"][:, 1], dic["bnd"][:, 0], linewidth=dic["lw"])
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['cwd']}/{dic['fol']}/extracted_border.png", dpi=600)

    # Save the interior grains
    fig, axis = plt.subplots()
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray"],
    )
    lmax = 0
    for contour in dic["cn_grains"]:
        bng = measure.approximate_polygon(contour, tolerance=dic["tol_grains"])
        if len(contour) > 3:
            axis.plot(bng[:, 1], bng[:, 0], linewidth=dic["lw"])
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['cwd']}/{dic['fol']}/interior_grains.png", dpi=600)

    # Save the extracted border + interior grains
    fig, axis = plt.subplots()
    axis.imshow(
        dic["im"][dic["ad_bord"] : -dic["ad_bord"], dic["ad_bord"] : -dic["ad_bord"]],
        cmap=mpl.colormaps["gray"],
    )
    axis.plot(
        dic["bnd"][:, 1] - dic["ad_bord"],
        dic["bnd"][:, 0] - dic["ad_bord"],
        linewidth=dic["lw"],
    )
    lmax = 0
    for contour in dic["cn_grains"]:
        bng = measure.approximate_polygon(contour, tolerance=dic["tol_grains"])
        if len(contour) > 3:
            axis.plot(bng[:, 1], bng[:, 0], linewidth=dic["lw"])
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{dic['cwd']}/{dic['fol']}/interior_grains_border.png", dpi=600)
    return dic


def extract_borders(dic):
    """
    Function to extract the borders of the image

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["pl"] = []
    dic["pb"] = []
    dic["pr"] = []
    dic["pt"] = []
    dic["aa"] = 0
    dic["dd"] = 0
    dic["cc"] = 0
    dic["bb"] = min(dic["bnd"][:, 0])
    dic["bl"] = min(dic["bnd"][:, 1])
    dic["bt"] = max(dic["bnd"][:, 0])
    dic["br"] = max(dic["bnd"][:, 1])
    for i in range(len(dic["bnd"]) - 2):
        if dic["bnd"][-i - 1, 0] > dic["bb"] + 1 and dic["aa"] == 0:
            dic["pr"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["imH"] - dic["bnd"][-i - 1, 0] + dic["ad_bord"],
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
                    dic["imH"] - dic["bnd"][-i - 1, 0] + dic["ad_bord"],
                ]
            )
        if dic["bnd"][-i - 1, 1] < dic["bl"] + 1:
            dic["dd"] = 1
        if (dic["bnd"][-i - 1, 0] > dic["bb"] + 1 and dic["dd"] == 1) and (
            dic["cc"] == 0 and len(dic["pb"]) > 0
        ):
            dic["pl"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["imH"] - dic["bnd"][-i - 1, 0] + dic["ad_bord"],
                ]
            )
        if dic["bnd"][-i - 1 - 1, 0] > dic["bt"] - 1 and dic["aa"] == 1:
            dic["cc"] = 1
        if len(dic["pl"]) > 0 + 1 and dic["cc"] == 1:
            dic["pt"].append(
                [
                    dic["bnd"][-i - 1, 1] - dic["ad_bord"],
                    dic["imH"] - dic["bnd"][-i - 1, 0] + dic["ad_bord"],
                ]
            )
    return dic


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
    dic["point"].append([dic["bl"] - dic["ad_bord"], dic["bb"] + 1 - dic["ad_bord"]])
    for i in range(len(dic["pl"])):
        dic["point"].append(
            [
                dic["pl"][len(dic["pl"]) - 1 - i][0],
                dic["pl"][len(dic["pl"]) - 1 - i][1],
            ]
        )
    dic["point"].append([dic["bl"] - dic["ad_bord"], dic["bt"] + 1 - dic["ad_bord"]])
    for i in range(len(dic["pb"]) - 1):
        dic["point"].append(
            [
                dic["pb"][len(dic["pb"]) - 1 - i][0],
                dic["pb"][len(dic["pb"]) - 1 - i][1],
            ]
        )
    dic["point"].append([dic["br"] - dic["ad_bord"], dic["bt"] + 1 - dic["ad_bord"]])
    for i in range(len(dic["pr"]) - 1):
        dic["point"].append(
            [
                dic["pr"][len(dic["pr"]) - 1 - i][0],
                dic["pr"][len(dic["pr"]) - 1 - i][1],
            ]
        )
    dic["point"].append([dic["br"] - dic["ad_bord"], dic["bb"] + 1 - dic["ad_bord"]])
    for i in range(len(dic["pt"]) - 2):
        dic["point"].append(
            [
                dic["pt"][len(dic["pt"]) - 1 - i][0],
                dic["pt"][len(dic["pt"]) - 1 - i][1],
            ]
        )
    dic["point"].append([dic["bl"] - dic["ad_bord"], dic["bb"] + 1 - dic["ad_bord"]])
    return dic


def boundary_tags_left_bottom(dic):
    """
    Function to identify the wall, left, and bottom boundary tags

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["bdnL"] = []
    dic["bdnT"] = []
    dic["wall"] = []
    dic["j"] = 0
    for _ in range(len(dic["pl"]) + 1):
        if (
            abs(dic["bl"] - dic["ad_bord"] - dic["point"][dic["j"]][0]) < 0.1
            and abs(dic["bl"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][0]) < 0.1
        ):
            dic["bdnL"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1
    for _ in range(len(dic["pb"])):
        if (
            abs(dic["bt"] + 1.0 - dic["ad_bord"] - dic["point"][dic["j"]][1]) < 0.1
            and abs(dic["bt"] + 1.0 - dic["ad_bord"] - dic["point"][dic["j"] + 1][1])
            < 0.1
        ):
            dic["bdnT"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1
    return dic


def boundary_tags_right_top(dic):
    """
    Function to identify the wall, right, and top boundary tags

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    dic["bdnR"] = []
    dic["bdnB"] = []
    for _ in range(len(dic["pr"])):
        if (
            abs(dic["br"] - dic["ad_bord"] - dic["point"][dic["j"]][0]) < 0.1
            and abs(dic["br"] - dic["ad_bord"] - dic["point"][dic["j"] + 1][0]) < 0.1
        ):
            dic["bdnR"].append(dic["j"])
        else:
            dic["wall"].append(dic["j"])
        dic["j"] += 1
    if len(dic["pt"]) == 0:
        dic["bdnB"].append(dic["j"])
    else:
        for _ in range(len(dic["pt"]) - 1):
            if (
                abs(dic["bb"] + 1.0 - dic["ad_bord"] - dic["point"][dic["j"]][1]) < 0.1
                and abs(
                    dic["bb"] + 1.0 - dic["ad_bord"] - dic["point"][dic["j"] + 1][1]
                )
                < 0.1
            ):
                dic["bdnB"].append(dic["j"])
            else:
                dic["wall"].append(dic["j"])
            dic["j"] += 1
    return dic


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
    filled_template = mytemplate.render(**var)
    with open(f"{dic['cwd']}/{dic['fol']}/mesh.geo", "w", encoding="utf8") as file:
        file.write(filled_template)
    for contour in dic["cn_grains"]:
        contour = measure.approximate_polygon(contour, tolerance=dic["tol_grains"])
        if len(contour) > 3:
            with open(
                f"{dic['cwd']}/{dic['fol']}/mesh.geo", "r", encoding="utf8"
            ) as file:
                dic["geo"] = file.readlines()
            dic["p"] = []
            dic["ng"] = 0
            for k in enumerate(dic["geo"]):
                if dic["geo"][k[0]][:5] == "Plane":
                    dic["l1"] = k[0]
                if dic["geo"][k[0]][-6:-1] == "= hs;":
                    dic["ng"] += 1
                if dic["geo"][k[0]][:6] == "Mesh 3":
                    dic["lf"] = k[0]
            for i in range(len(contour) - 1):
                dic["p"].append([contour[i, 1], dic["imH"] - contour[i, 0]])

            # Update the .geo file adding a new grain
            mytemplate = Template(
                filename=f"{dic['pat']}/templates/utils/add_grain.mako"
            )
            var = {"dic": dic}
            filled_template = mytemplate.render(**var)
            with open(
                f"{dic['cwd']}/{dic['fol']}/mesh.geo", "w", encoding="utf8"
            ) as file:
                file.write(filled_template)

    os.system(f"{dic['gmsh_path']} {dic['cwd']}/{dic['fol']}/mesh.geo -3 & wait")
    return dic


def run_stokes(dic):
    """
    Function to write the openFOAM files to run the Navier-Stokes flow simulations

    Args:
        dic (dict): Global dictionary with required parameters

    Returns:
        dic (dict): Global dictionary with new added parameters
    """
    var = {"dic": dic}
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM")
    os.system(f"rm -rf {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/0")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/constant")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/system")
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
            f"{dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/{file}",
            "w",
            encoding="utf8",
        ) as file:
            file.write(filled_template)
    os.system(
        f"cp {dic['cwd']}/{dic['fol']}/mesh.msh {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes"
    )
    os.chdir(f"{dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes")
    os.system("gmshToFoam mesh.msh & wait")

    with open("constant/polyMesh/boundary", "r", encoding="utf8") as file:
        dic["boundary"] = file.readlines()
        dic["boundary"][20] = "type      empty;"
    mytemplate = Template(filename=f"{dic['pat']}/templates/utils/boundary.mako")
    var = {"dic": dic}
    filled_template = mytemplate.render(**var)
    with open("constant/polyMesh/boundary", "w", encoding="utf8") as file:
        file.write(filled_template)

    os.system(f"rm -rf {dic['cwd']}/{dic['fol']}/VTK_flowStokes")
    # Running the steady-state flow simulation
    os.system("foamRun -solver incompressibleFluid & wait")
    os.system("foamToVTK & wait")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/VTK_flowStokes")
    os.system(f"cp -r VTK/* {dic['cwd']}/{dic['fol']}/VTK_flowStokes")
    return dic


def run_tracer(dic):
    """
    Function to write the openFOAM files to run the Tracer flow simulations

    Args:
        dic (dict): Global dictionary with required parameters
    """
    os.chdir(f"{dic['cwd']}")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/VTK_tracerTransport")
    os.system(f"rm -rf {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/0")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/constant")
    os.system(f"mkdir {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/system")
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
            f"{dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/{file}",
            "w",
            encoding="utf8",
        ) as file:
            file.write(filled_template)
    os.chdir(f"{dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes")
    list_of_folders = glob.glob(f"{dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/*/")
    list_of_folders.remove(max(list_of_folders, key=os.path.getctime))
    latest_folder = max(list_of_folders, key=os.path.getctime)
    os.system(
        f"cp {latest_folder}U {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/0/"
    )
    os.system(
        f"cp {latest_folder}p {dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/0/"
    )
    os.system(
        f"cp -r {dic['cwd']}/{dic['fol']}/OpenFOAM/flowStokes/constant/polyMesh "
        f"{dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport/constant/"
    )
    os.chdir(f"{dic['cwd']}/{dic['fol']}/OpenFOAM/tracerTransport")
    os.system("topoSet & wait")

    # Running the simulation of tracer transport
    os.system("foamRun & wait")
    # exit()
    os.system("foamToVTK & wait")
    os.system(f"cp -r VTK/* {dic['cwd']}/{dic['fol']}/VTK_tracerTransport")


def main():
    """Main function"""
    pymm()


# {
# Copyright 2022, NORCE Norwegian Research Centre AS, Computational
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
