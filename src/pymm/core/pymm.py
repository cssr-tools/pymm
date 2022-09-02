#!/usr/bin/env python3

""""
Script to run the image-based workflow 
on a microsystem configuration 
"""

import os
import csv
import glob
import argparse
import numpy as np
import porespy as ps
import matplotlib.pyplot as plt
from skimage import io, measure
from skimage.transform import rescale
from mako.template import Template


def pymm():
    """Run the workflow on a microsystem configuration"""
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
        help="The configuration of the microsystem, currently only image and device supported ('image' by default).",
    )
    parser.add_argument(
        "-t",
        "--type",
        default="all",
        help="Run the whole framework ('all'), only the mesh part ('mesh'), keep the current mesh and only the flow ('flow'), flow and tracer ('flowntracer'), or only tracer ('tracer') ('all' by default).",
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
        help="The full path to the gmsh executable or simple Gmsh if it runs from the terminal ('gmsh' by default).",
    )
    parser.parse_args()
    cmdArgs = vars(parser.parse_args())
    in_file = cmdArgs["parameters"]  # Name of the input file
    in_image = cmdArgs["image"]  # Name of the image file
    out_fol = cmdArgs["output"]  # Name for the output folder
    gmsh_path = cmdArgs["gmsh"]  # Command to execute gmsh
    wtr = cmdArgs["type"]  # Parts of the workflow to run
    mode = cmdArgs["mode"]  # Configuration of the microsystem
    pat = os.path.dirname(__file__)[:-5]  # Path to the pyff folder
    cwd = os.getcwd()  # Path to the folder of the parameters.txt file
    lol = []

    """Read the input values"""
    for row in csv.reader(open(in_file), delimiter="#"):
        lol.append(row)
    Ls = float(lol[1][0])  # Length of the microsystem [m]
    Hs = float(lol[2][0])  # Heigth of the microsystem [m]
    Ds = float(lol[3][0])  # Depth of the microsystem [m]
    thr = int(lol[4][0])  # Threshold for converting the image to binary
    res = float(lol[5][0])  # rescaled factor for the image
    size_grains = int(lol[6][0])  # Minimum size of the grain clusters [pixels]
    tol_border = float(lol[7][0])  # Tolerance to approximate the border as polygon
    tol_grains = float(lol[8][0])  # Tolerance to approximate the grains as polygon
    lw = float(lol[9][0])  # Line width to show the contours in the produced figures
    Cs = float(
        lol[10][0]
    )  # Width of the top and bottom channels in the micromodel device [m]
    hz = float(lol[11][0])  # Mesh size [m]
    nu = float(
        lol[12][0]
    )  # Fluid kinematic viscocity [Dynamic viscocity/fluid_density, m2/s]
    D = float(lol[13][0])  # Diffusion coefficient for the tracer [m2/s]
    bc_inlet = float(
        lol[14][0]
    )  # Inlet boundary condition (Pressure/fluid_density, [Pa/(kg/m3)])
    t_et = float(lol[15][0])  # End time for the tracer simulation [s]
    t_wi = float(lol[16][0])  # Time interval to write the tracer results [s]
    p_tol = float(
        lol[17][0]
    )  # Convergence criterium for the pressure solution in the numerical scheme for the Stokes simulation
    u_tol = float(
        lol[18][0]
    )  # Convergence criterium for the velocity solution in the numerical scheme for the Stokes simulation
    f_maxI = float(
        lol[19][0]
    )  # Maximum number of iterations for the Stokes simulation in case the convergence criteria have not been reached
    t_dt = float(
        lol[20][0]
    )  # Time step in the numerical scheme for the Tracer simulation [s]

    if wtr == "all" or wtr == "mesh":
        """Read the image"""
        im0 = np.array(io.imread(in_image))

        """ Convert the image to binary (black and white) and rescale"""
        im = []
        for i in range(im0.shape[0]):
            imbr = []
            for j in range(im0.shape[1]):
                if i == 0 or i == im0.shape[0] - 1 or j == 0 or j == im0.shape[1] - 1:
                    imbr.append(0 == 0)
                elif (i == 1 or i == im0.shape[0] - 2) and mode == "device":
                    imbr.append(0 == 1)
                elif im0[i][j][2] > thr:
                    imbr.append(0 == 1)
                else:
                    imbr.append(0 == 0)
            im.append(imbr)
        im = np.array(im)
        im = rescale(im, res)
        imH = im.shape[0]
        imL = im.shape[1]

        """ Add arbitrary border to extract the image boundaries """
        adB = 50
        im = np.pad(im, adB, pad_with, padder=1)

        """ Save the binary image for visualization """
        os.system(f"rm -rf {cwd}/{out_fol}")
        os.system(f"mkdir {cwd}/{out_fol}")
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow(im[adB:-adB, adB:-adB], cmap=plt.cm.gray)
        fig.savefig(f"{cwd}/{out_fol}/binary_image.png", dpi=600)

        """ Extract the contour of the grains on the image border and interior """
        border = ps.filters.trim_small_clusters(im, size=(imH + 2 * imL) * adB)
        cn_border = measure.find_contours(
            border, 0.5, fully_connected="high", positive_orientation="high"
        )
        grains = ps.filters.trim_small_clusters(
            np.logical_and(np.bitwise_not(border), im), size=size_grains
        )
        grains = grains[adB:-adB, adB:-adB]
        cn_grains = measure.find_contours(
            grains, 0.5, fully_connected="high", positive_orientation="high"
        )

        """ Save the extracted border for visualization """
        ps.visualization.set_mpl_style()
        fig, ax = plt.subplots()
        ax.imshow(border, cmap=plt.cm.gray)
        lmax = 0
        for contour in cn_border:
            contour = measure.approximate_polygon(contour, tolerance=tol_border)
            peri = max(
                (contour[:, 0] - np.roll(contour[:, 0], 1)) ** 2
                + (contour[:, 1] - np.roll(contour[:, 1], 1)) ** 2
            )
            if peri > lmax:
                lmax = peri
                bnd = contour
        ax.plot(bnd[:, 1], bnd[:, 0], linewidth=lw)
        ax.axis("image")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.savefig(f"{cwd}/{out_fol}/extracted_border.png", dpi=600)

        """ Save the interior grains """
        fig, ax = plt.subplots()
        ax.imshow(im[adB:-adB, adB:-adB], cmap=plt.cm.gray)
        lmax = 0
        for contour in cn_grains:
            bng = measure.approximate_polygon(contour, tolerance=tol_grains)
            if len(contour) > 3:
                ax.plot(bng[:, 1], bng[:, 0], linewidth=lw)
        ax.axis("image")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.savefig(f"{cwd}/{out_fol}/interior_grains.png", dpi=600)

        """ Save the extracted border + interior grains """
        fig, ax = plt.subplots()
        ax.imshow(im[adB:-adB, adB:-adB], cmap=plt.cm.gray)
        ax.plot(bnd[:, 1] - adB, bnd[:, 0] - adB, linewidth=lw)
        lmax = 0
        for contour in cn_grains:
            bng = measure.approximate_polygon(contour, tolerance=tol_grains)
            if len(contour) > 3:
                ax.plot(bng[:, 1], bng[:, 0], linewidth=lw)
        ax.axis("image")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.savefig(f"{cwd}/{out_fol}/interior_grains_border.png", dpi=600)

        """ Extract the coordinates of the left (pl) and right (pr) borders """
        pl = []
        pb = []
        pr = []
        pt = []
        aa = 0
        dd = 0
        cc = 0
        bb = min(bnd[:, 0])
        bl = min(bnd[:, 1])
        bt = max(bnd[:, 0])
        br = max(bnd[:, 1])
        for i in range(len(bnd) - 2):
            if bnd[-i - 1, 0] > bb + 1 and aa == 0:
                pr.append([bnd[-i - 1, 1] - adB, imH - bnd[-i - 1, 0] + adB])
            else:
                aa = 1
            if (bnd[-i - 1, 1] > bl + 1 and aa == 1) and len(pl) == 0:
                pb.append([bnd[-i - 1, 1] - adB, imH - bnd[-i - 1, 0] + adB])
            if bnd[-i - 1, 1] < bl + 1:
                dd = 1
            if (bnd[-i - 1, 0] > bb + 1 and dd == 1) and (cc == 0 and len(pb) > 0):
                pl.append([bnd[-i - 1, 1] - adB, imH - bnd[-i - 1, 0] + adB])
            if bnd[-i - 1 - 1, 0] > bt - 1 and aa == 1:
                cc = 1
            if len(pl) > 0 + 1 and cc == 1:
                pt.append([bnd[-i - 1, 1] - adB, imH - bnd[-i - 1, 0] + adB])

        """ Identify the boundary tags """
        Point = []
        bdnL = []
        bdnT = []
        bdnR = []
        bdnB = []
        wall = []
        Point.append([bl - adB, bb + 1 - adB])
        for i in range(len(pl)):
            Point.append([pl[len(pl) - 1 - i][0], pl[len(pl) - 1 - i][1]])
        Point.append([bl - adB, bt + 1 - adB])
        for i in range(len(pb) - 1):
            Point.append([pb[len(pb) - 1 - i][0], pb[len(pb) - 1 - i][1]])
        Point.append([br - adB, bt + 1 - adB])
        for i in range(len(pr) - 1):
            Point.append([pr[len(pr) - 1 - i][0], pr[len(pr) - 1 - i][1]])
        Point.append([br - adB, bb + 1 - adB])
        for i in range(len(pt) - 2):
            Point.append([pt[len(pt) - 1 - i][0], pt[len(pt) - 1 - i][1]])
        Point.append([bl - adB, bb + 1 - adB])
        n = 0

        for i in range(len(pl) + 1):
            if (
                abs(bl - adB - Point[n][0]) < 0.1
                and abs(bl - adB - Point[n + 1][0]) < 0.1
            ):
                bdnL.append(n)
            else:
                wall.append(n)
            n += 1
        for i in range(len(pb)):
            if (
                abs(bt + 1.0 - adB - Point[n][1]) < 0.1
                and abs(bt + 1.0 - adB - Point[n + 1][1]) < 0.1
            ):
                bdnT.append(n)
            else:
                wall.append(n)
            n += 1
        for i in range(len(pr)):
            if (
                abs(br - adB - Point[n][0]) < 0.1
                and abs(br - adB - Point[n + 1][0]) < 0.1
            ):
                bdnR.append(n)
            else:
                wall.append(n)
            n += 1

        if len(pt) == 0:
            bdnB.append(n)
        else:
            for i in range(len(pt) - 1):
                if (
                    abs(bb + 1.0 - adB - Point[n][1]) < 0.1
                    and abs(bb + 1.0 - adB - Point[n + 1][1]) < 0.1
                ):
                    bdnB.append(n)
                else:
                    wall.append(n)
                n += 1

        """ Write the .geo file"""
        mytemplate = Template(filename=pat + f"/templates/grid/{mode}.mako")
        var = {
            "pl": pl,
            "pr": pr,
            "pb": pb,
            "pt": pt,
            "bdnL": bdnL,
            "bdnR": bdnR,
            "bdnB": bdnB,
            "bdnT": bdnT,
            "wall": wall,
            "imL": imL,
            "imH": imH,
            "Ls": Ls,
            "Hs": Hs,
            "Ds": Ds,
            "Cs": Cs,
            "hz": hz,
        }
        FilledTemplate = mytemplate.render(**var)
        with open(f"{cwd}/{out_fol}/mesh.geo", "w") as f:
            f.write(FilledTemplate)
        for contour in cn_grains:
            contour = measure.approximate_polygon(contour, tolerance=tol_grains)
            if len(contour) > 3:
                with open(f"{cwd}/{out_fol}/mesh.geo", "r") as f:
                    lol = f.readlines()
                p = []
                ng = 0
                lf = 0
                for k in range(len(lol)):
                    if lol[k][:5] == "Plane":
                        l1 = k
                    if lol[k][-6:-1] == "= hs;":
                        ng += 1
                    if lol[k][:6] == "Mesh 3":
                        lf = k
                for i in range(len(contour) - 1):
                    p.append([contour[i, 1], imH - contour[i, 0]])

                """Update the .geo file adding a new grain"""
                mytemplate = Template(filename=pat + "/templates/utils/add_grain.mako")
                var = {"lol": lol, "p": p, "l1": l1, "ng": ng, "lf": lf}
                FilledTemplate = mytemplate.render(**var)
                with open(f"{cwd}/{out_fol}/mesh.geo", "w") as f:
                    f.write(FilledTemplate)

        os.system(f"{gmsh_path} {cwd}/{out_fol}/mesh.geo -3 & wait")

    if (wtr == "all" or wtr == "flow") or wtr == "flowntracer":
        """Setting up of the files for the OpenFOAM simulations"""
        var = {
            "bc_inlet": bc_inlet,
            "f_maxI": f_maxI,
            "nu": nu,
            "p_tol": p_tol,
            "u_tol": u_tol,
        }
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM")
        os.system(f"rm -rf {cwd}/{out_fol}/OpenFOAM/flowStokes")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/flowStokes")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/flowStokes/0")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/flowStokes/constant")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/flowStokes/system")
        for file in [
            "0/p",
            "0/U",
            "constant/transportProperties",
            "constant/turbulenceProperties",
            "system/controlDict",
            "system/fvSchemes",
            "system/fvSolution",
        ]:
            mytemplate = Template(
                filename=pat + f"/templates/OpenFOAM/flowStokes/{file}.mako"
            )
            FilledTemplate = mytemplate.render(**var)
            with open(f"{cwd}/{out_fol}/OpenFOAM/flowStokes/{file}", "w") as f:
                f.write(FilledTemplate)
        os.system(f"cp {cwd}/{out_fol}/mesh.msh {cwd}/{out_fol}/OpenFOAM/flowStokes")
        os.chdir(f"{cwd}/{out_fol}/OpenFOAM/flowStokes")
        os.system("gmshToFoam mesh.msh & wait")

        with open("constant/polyMesh/boundary", "r") as f:
            lol = f.readlines()
            lol[22] = "type      empty;"
        mytemplate = Template(filename=pat + "/templates/utils/boundary.mako")
        var = {"lol": lol}
        FilledTemplate = mytemplate.render(**var)
        with open("constant/polyMesh/boundary", "w") as f:
            f.write(FilledTemplate)

        os.system(f"rm -rf {cwd}/{out_fol}/VTK_flowStokes")
        """ Running the steady-state flow simulation """
        os.system("simpleFoam & wait")
        os.system("foamToVTK & wait")
        os.system(f"mkdir {cwd}/{out_fol}/VTK_flowStokes")
        os.system(f"cp -r VTK/* {cwd}/{out_fol}/VTK_flowStokes")

    if (wtr == "all" or wtr == "flowntracer") or wtr == "tracer":
        os.chdir(f"{cwd}")
        os.system(f"mkdir {cwd}/{out_fol}/VTK_tracerTransport")
        """ Setting up of the files for the tracer simulations"""
        os.system(f"rm -rf {cwd}/{out_fol}/OpenFOAM/tracerTransport")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/tracerTransport")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/tracerTransport/0")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/tracerTransport/constant")
        os.system(f"mkdir {cwd}/{out_fol}/OpenFOAM/tracerTransport/system")
        var = {"D": D, "t_dt": t_dt, "t_et": t_et, "t_wi": t_wi}
        for file in [
            "inlet",
            "0/T",
            "constant/transportProperties",
            "constant/fvOptions",
            "system/controlDict",
            "system/fvSchemes",
            "system/fvSolution",
        ]:
            mytemplate = Template(
                filename=pat + f"/templates/OpenFOAM/tracerTransport/{file}.mako"
            )
            FilledTemplate = mytemplate.render(**var)
            with open(f"{cwd}/{out_fol}/OpenFOAM/tracerTransport/{file}", "w") as f:
                f.write(FilledTemplate)
        os.chdir(f"{cwd}/{out_fol}/OpenFOAM/flowStokes")
        list_of_folders = glob.glob(f"{cwd}/{out_fol}/OpenFOAM/flowStokes/*/")
        list_of_folders.remove(max(list_of_folders, key=os.path.getctime))
        latest_folder = max(list_of_folders, key=os.path.getctime)
        os.system(f"cp {latest_folder}U {cwd}/{out_fol}/OpenFOAM/tracerTransport/0/")
        os.system(
            f"cp -r {cwd}/{out_fol}/OpenFOAM/flowStokes/constant/polyMesh {cwd}/{out_fol}/OpenFOAM/tracerTransport/constant/"
        )
        os.chdir(f"{cwd}/{out_fol}/OpenFOAM/tracerTransport")
        os.system("setSet -batch inlet & wait")

        """ Running the simulation of tracer transport """
        os.system("scalarTransportFoam & wait")
        os.system("foamToVTK & wait")
        os.system(f"mkdir {cwd}/{out_fol}/VTK_tracerTransport")
        os.system(f"cp -r VTK/* {cwd}/{out_fol}/VTK_tracerTransport")


def pad_with(vector, pad_width, iaxis, kwargs):
    """Function to add extra border to later extract the image boundaries"""
    pad_value = kwargs.get("padder", 10)
    vector[: pad_width[0]] = pad_value
    vector[-pad_width[1] :] = pad_value


def main():
    pymm()


# {
# Copyright 2022, NORCE Norwegian Research Centre AS, Computational
# Geosciences and Modelling.

# This file is part of the pymm module.

# pymm is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ad-wa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this file.  If not, see <http://www.gnu.org/licenses/>.
# }
