# SPDX-FileCopyrightText: 2022-2026 NORCE Research AS
# SPDX-License-Identifier: GPL-3.0
# pylint: disable=R0902,R0912,R0913,R0914,R0915,R0917,E1102,E1123,C0103

"""Main script for pymm"""

import argparse
import sys
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from contextlib import nullcontext
import tomllib
from typing import Any
import numpy as np
from numpy.typing import NDArray
import skimage.transform
from skimage import io, measure
from skimage.morphology import remove_small_objects
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from alive_progress import alive_bar
from mako.template import Template

ADD_BORDER = 50  # Add arbitrary border to extract the image boundaries


@dataclass(slots=True, frozen=True)
class PymmConfig:
    """Central configuration object for pymm from TOML inputs"""

    length: float
    width: float
    thickness: float
    grainMeaning: int
    threshold: float
    rescale: float
    grainsSize: int
    borderTol: float
    grainsTol: float
    lineWidth: float
    channelWidth: float
    meshSize: float
    viscosity: float
    diffusion: float
    inletLocation: str
    inletValue: float
    tracerTime: float
    tracerWrite: float
    pressureConv: float
    velocityConv: float
    iterationsMax: int
    tracerStep: float


def main() -> None:
    """Python for microsystems"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Main script to run the workflow on a microsystem configuration.",
    )
    parser.add_argument(
        "-i",
        "--image",
        type=str.strip,
        default="microsystem.png",
        help="The base name of the image",
    )
    parser.add_argument(
        "-p",
        "--parameters",
        type=str.strip,
        default="parameters.toml",
        help="The base name of the parameter file",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str.strip,
        choices=["image", "device"],
        default="image",
        help="The setup configuration of the microsystem",
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str.strip,
        choices=["pngs", "mesh", "flow", "mesh_flow", "flow_tracer", "tracer", "all"],
        default="mesh",
        help="Run the whole framework ('all'), only the generation of the PNG figures "
        "with the segmentation to grains, voids, and boundary ('pngs'), the mesh files "
        "for Gmsh ('mesh'), keep the current mesh and only simulate the flow velocity "
        "field ('flow'), mesh and flow ('mesh_flow'), flow and tracer ('flow_tracer'), "
        "or only tracer simulations ('tracer')",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str.strip,
        default="output",
        help="The base name of the output folder",
    )
    parser.add_argument(
        "-g",
        "--gmsh",
        type=str.strip,
        default="gmsh",
        help="The full path to the gmsh executable or simple Gmsh if it runs from the "
        "terminal",
    )
    pat = Path(__file__).resolve().parent.parent
    cmdargs = vars(parser.parse_known_args()[0])
    fol = Path(cmdargs["output"].strip()).resolve()
    gmsh = cmdargs["gmsh"]
    mode = cmdargs["mode"]
    kind = cmdargs["type"]
    image_path = cmdargs["image"]
    parameters_path = Path(cmdargs["parameters"])
    if not parameters_path.exists():
        print(f"The file {cmdargs['parameters']} is not found.")
        sys.exit()
    if parameters_path.suffix == ".txt":
        print("toml is used now for the parameter file; please update the file.")
        sys.exit()
    with open(parameters_path, "rb") as f:
        toml = tomllib.load(f)
    cfg = PymmConfig(**toml)
    print("\nExecuting pymm, please wait.")
    if kind in {"all", "pngs", "mesh", "mesh_flow"}:
        # Generate the image
        imH, imL, cn_grains, boundary = process_image(cfg, fol, mode, image_path)
        # Extract the coordinates of the image borders
        pl, pt, pr, pb, bb, bl, bt, br = extract_borders(boundary)
        if kind in {"all", "mesh", "mesh_flow"}:
            if cfg.inletLocation.lower() not in {"left", "top", "right", "bottom"}:
                print(f"Invalid inletLocation {cfg.inletLocation}.")
                sys.exit()
            bdnL: list[int] = []
            bdnT: list[int] = []
            bdnR: list[int] = []
            bdnB: list[int] = []
            wall: list[int] = []
            if mode == "image":
                # Set the boundary tags
                points = np.vstack([pl, pt[1:], pr, pb])
                points = np.vstack([points, points[0]])
                bdnL, bdnT, index = boundary_tags_left_top(points, pl, pt, bl, bt, wall)
                bdnR, bdnB = boundary_tags_right_bottom(
                    points, index, pr, pb, bb, br, wall
                )
            # Write the .geo file
            write_geo(
                cfg,
                fol,
                pat,
                mode,
                gmsh,
                imH,
                imL,
                cn_grains,
                pl,
                pt,
                pr,
                pb,
                bdnL,
                bdnT,
                bdnR,
                bdnB,
                wall,
            )
    if kind in {"all", "mesh_flow", "flow", "flow_tracer"}:
        # Set up of the files for the Flow simulations and run them
        if not (fol / "mesh.msh").exists():
            print("Run first either -t all or -t mesh.")
            sys.exit()
        run_stokes(cfg, fol, pat)
    if kind in {"all", "flow_tracer", "tracer"}:
        if not (fol / "OpenFOAM" / "flowStokes").exists():
            print("Run first either -t all or -t mesh_flow.")
            sys.exit()
        # Set up of the files for the Tracer simulations and run them
        run_tracer(cfg, fol, pat)
    print(
        "\nThe execution of pymm succeeded. "
        + f"The generated files have been written to {fol}\n"
    )


def process_image(
    cfg: PymmConfig, fol: Path, mode: str, in_image: str
) -> tuple[int, int, list[NDArray[np.float64]], NDArray[np.float64]]:
    """Function to process the input image"""
    # Read the image
    im0 = np.array(io.imread(in_image, as_gray=True))
    # Convert the image to binary (black and white) and rescale
    meaning = 1 - 2 * cfg.grainMeaning
    threshold_scaled = meaning * cfg.threshold
    flipped = im0[::-1]
    im = ~(meaning * flipped < threshold_scaled)
    im[0, :] = True
    im[-1, :] = True
    im[:, 0] = True
    im[:, -1] = True
    if mode == "device" and im.shape[0] > 2 and im.shape[1] > 2:
        im[1, 1:-1] = False
        im[-2, 1:-1] = False
    im = skimage.transform.rescale(im, cfg.rescale)
    imH, imL = im.shape[0], im.shape[1]

    im = np.pad(im, ADD_BORDER, pad_with, padder=1)

    # Save the binary image for visualization
    fol.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots()
    axis.imshow(
        im[ADD_BORDER:-ADD_BORDER, ADD_BORDER:-ADD_BORDER],
        cmap=mpl.colormaps["gray_r"],
    )
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{fol}/binary_image.png", dpi=600)

    # Extract the contour of the grains on the image border and interior
    border = remove_small_objects(im, max_size=(imH + 2 * imL) * ADD_BORDER)
    grains = remove_small_objects(~(border) & im, max_size=cfg.grainsSize)
    cn_border = measure.find_contours(
        border, 0.5, fully_connected="high", positive_orientation="high"
    )
    grains = grains[ADD_BORDER:-ADD_BORDER, ADD_BORDER:-ADD_BORDER]
    cn_grains = measure.find_contours(
        grains, 0.5, fully_connected="high", positive_orientation="high"
    )
    boundary = make_figures(cfg, fol, im, border, cn_grains, cn_border)
    return imH, imL, cn_grains, boundary


def make_figures(
    cfg: PymmConfig,
    fol: Path,
    im: NDArray[np.bool_],
    border: NDArray[np.bool_],
    cn_grains: list[NDArray[np.float64]],
    cn_border: list[NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Function to make figures with the extract grains and contours"""
    slices = slice(ADD_BORDER, -ADD_BORDER)
    image_slice = (slices, slices)
    fig, axis = plt.subplots()
    axis.imshow(border[image_slice], cmap=mpl.colormaps["gray_r"])
    lmax, boundary = 0, np.empty(0)
    for contour in cn_border:
        contour = measure.approximate_polygon(contour, tolerance=cfg.borderTol)
        peri = np.max(
            (contour[:, 0] - np.roll(contour[:, 0], 1)) ** 2
            + (contour[:, 1] - np.roll(contour[:, 1], 1)) ** 2
        )
        if peri > lmax:
            lmax = peri
            boundary = contour
    shifted_border_x = boundary[:, 1] - ADD_BORDER
    shifted_border_y = boundary[:, 0] - ADD_BORDER
    axis.plot(shifted_border_x, shifted_border_y, linewidth=cfg.lineWidth)
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{fol}/extracted_border.png", dpi=600)

    fig, axis = plt.subplots()
    axis.imshow(im[image_slice], cmap=mpl.colormaps["gray_r"])
    grain_lines = []
    for contour in cn_grains:
        if len(contour) > 3:
            approximated = measure.approximate_polygon(contour, tolerance=cfg.grainsTol)
            grain_lines.append((approximated[:, 1], approximated[:, 0]))
    segments = [np.column_stack((x_vals, y_vals)) for x_vals, y_vals in grain_lines]
    axis.add_collection(LineCollection(segments, linewidths=cfg.lineWidth, color="red"))
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{fol}/interior_grains.png", dpi=600)

    fig, axis = plt.subplots()
    axis.imshow(im[image_slice], cmap=mpl.colormaps["gray_r"])
    axis.plot(shifted_border_x, shifted_border_y, linewidth=cfg.lineWidth)
    segments = [np.column_stack((x_vals, y_vals)) for x_vals, y_vals in grain_lines]
    axis.add_collection(LineCollection(segments, linewidths=cfg.lineWidth, color="red"))
    axis.axis("image")
    axis.set_xticks([])
    axis.set_yticks([])
    fig.savefig(f"{fol}/interior_grains_border.png", dpi=600)
    return boundary[::-1]


def extract_borders(
    boundary: NDArray[np.float64],
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    float,
    float,
    float,
    float,
]:
    """Function to extract the borders of the image"""
    shifted = boundary - ADD_BORDER
    aa, dd, cc = 0, 0, 0
    pl_list: list[list[float]] = []
    pt_list: list[list[float]] = []
    pr_list: list[list[float]] = []
    pb_list: list[list[float]] = []
    bb, bl = np.min(boundary[:, 0]), np.min(boundary[:, 1])
    bt, br = np.max(boundary[:, 0]), np.max(boundary[:, 1])
    for idx in range(len(boundary) - 1):
        x_val = boundary[idx, 0]
        y_val = boundary[idx, 1]
        sx = shifted[idx, 0]
        sy = shifted[idx, 1]
        if x_val > bb + 1 and aa == 0:
            pr_list.append([sy, sx])
        else:
            aa = 1
        if (y_val > bl + 1 and aa == 1) and not pl_list:
            pb_list.append([sy, sx])
        if y_val < bl + 1:
            dd = 1
        if (x_val > bb - 1 and dd == 1) and (cc == 0 and pb_list):
            pl_list.append([sy, sx])
        if x_val > bt - 1 and aa == 1:
            cc = 1
        if len(pl_list) > 1 and cc == 1:
            pt_list.append([sy, sx])
    pl = np.array(pl_list, dtype=np.float64)
    pt = np.array(pt_list, dtype=np.float64)
    pr = np.array(pr_list, dtype=np.float64)
    pb = np.array(pb_list, dtype=np.float64)
    return pl, pt, pr, pb, bb, bl, bt, br


def pad_with(
    vector: NDArray[np.float64], pad_width: tuple[int, int], _iaxis: int, kwargs: dict
) -> None:
    """
    Function to add extra border to later extract the image boundaries
    see https://numpy.org/doc/stable/reference/generated/numpy.pad.html
    """
    pad_value = kwargs.get("padder", 10)
    vector[: pad_width[0]] = pad_value
    vector[-pad_width[1] :] = pad_value


def _assign_boundary(
    point: NDArray[np.float64],
    start_index: int,
    number_of_segments: int,
    reference_value: float,
    coordinate_index: int,
    target: list[int],
    wall: list[int],
) -> int:
    """Assign the boundary tags"""
    shifted_reference = reference_value - ADD_BORDER
    indices = np.arange(start_index, start_index + number_of_segments)
    values0 = point[indices, coordinate_index]
    values1 = point[indices + 1, coordinate_index]
    mask = (np.abs(shifted_reference - values0) < 1) & (
        np.abs(shifted_reference - values1) < 1
    )
    target.extend(indices[mask].tolist())
    wall.extend(indices[~mask].tolist())
    return start_index + number_of_segments


def boundary_tags_left_top(
    point: NDArray[np.float64],
    pl: NDArray[np.float64],
    pt: NDArray[np.float64],
    bl: float,
    bt: float,
    wall: list[int],
) -> tuple[list[int], list[int], int]:
    """Assign the boundary left-top tags"""
    bdnL: list[int] = []
    bdnT: list[int] = []
    index: int = 0
    index = _assign_boundary(point, index, len(pl) - 1, bl, 0, bdnL, wall)
    index = _assign_boundary(point, index, len(pt), bt, 1, bdnT, wall)
    return bdnL, bdnT, index


def boundary_tags_right_bottom(
    point: NDArray[np.float64],
    start_index: int,
    pr: NDArray[np.float64],
    pb: NDArray[np.float64],
    bb: float,
    br: float,
    wall: list[int],
) -> tuple[list[int], list[int]]:
    "Assign the boundary right-bottom tags"
    bdnR: list[int] = []
    bdnB: list[int] = []
    index: int = start_index
    index = _assign_boundary(point, index, len(pr), br, 0, bdnR, wall)
    if pb.size == 0:
        bdnB.append(index)
    else:
        index = _assign_boundary(point, index, len(pb), bb, 1, bdnB, wall)
    return bdnR, bdnB


def write_geo(
    cfg: PymmConfig,
    fol: Path,
    pat: Path,
    mode: str,
    gmsh: str,
    imH: int,
    imL: int,
    cn_grains: list[NDArray[np.float64]],
    pl: NDArray[np.float64],
    pt: NDArray[np.float64],
    pr: NDArray[np.float64],
    pb: NDArray[np.float64],
    bdnL: list[int],
    bdnT: list[int],
    bdnR: list[int],
    bdnB: list[int],
    wall: list[int],
) -> None:
    """Function to write the Gmsh .geo file"""
    mapping = {
        "left": ("L", "R"),
        "top": ("T", "B"),
        "right": ("R", "L"),
        "bottom": ("B", "T"),
    }
    inlet, outlet = mapping[cfg.inletLocation.lower()]

    pl -= 0.5
    pr += np.array([0.5, -0.5])

    if mode == "device":

        point_left_lines: list[str] = []
        append = point_left_lines.append
        for i, (x, y) in enumerate(pl, 1):
            append(f"Point(#Tp[]+{i}) = {{{x}*rL/L, {y}*rH/H, 0, hb}};")
        point_right_lines: list[str] = []
        append = point_right_lines.append
        for i, (x, y) in enumerate(pr, 1):
            append(f"Point(#Tp[]+{i}) = {{{x}*rL/L, {y}*rH/H, 0, hb}};")
    else:
        pt += np.array([0.5, -0.5])
        pb += np.array([0.5, -0.5])
        point_lines: list[str] = []
        append = point_lines.append
        idx = 1
        for arr, sl in (
            (pl, slice(None)),
            (pt, slice(1, None)),
            (pr, slice(None)),
            (pb, slice(None)),
        ):

            sub = arr[sl]
            for i in range(sub.shape[0]):
                x = sub[i, 0]
                y = sub[i, 1]
                append(f"Point(#Tp[]+{idx}) = {{{x}*rL/L, {y}*rH/H, 0, hb}};")
                idx += 1

        bdn_lines: list[str] = []
        bdn_lines_append = bdn_lines.append

        for idx in bdnL:
            val = idx + 2
            bdn_lines_append(f"bdnL[] += {{out[{val}]}};")
        for idx in bdnT:
            val = idx + 2
            bdn_lines_append(f"bdnT[] += {{out[{val}]}};")
        for idx in bdnR:
            val = idx + 2
            bdn_lines_append(f"bdnR[] += {{out[{val}]}};")
        for idx in bdnB:
            val = idx + 2
            bdn_lines_append(f"bdnB[] += {{out[{val}]}};")
        wall_slice = wall[:-1]
        for idx in wall_slice:
            val = idx + 2
            bdn_lines_append(f"bdnW[] += {{out[{val}]}};")

    grain_lines = []
    nog = 0
    show_progress = sys.stdout.isatty()
    if show_progress:
        bar_ctx = alive_bar(len(cn_grains), bar="fish")
    else:
        bar_ctx = nullcontext()
    with bar_ctx as bar_animation:
        for contour in cn_grains:
            if show_progress:
                bar_animation()
            contour = measure.approximate_polygon(contour, tolerance=cfg.grainsTol)
            points = contour[:-1][:, [1, 0]]
            if points.shape[0] > 2:
                nog += 1
                grain_lines.append('Tp[] = Point "*";')
                grain_lines.append(f"h({nog}) = hs;")
                for idx, (x, y) in enumerate(points, 1):
                    grain_lines.append(
                        f"Point(#Tp[]+{idx}) = {{(rL/L)*{x}, {y}*rH/H, 0, h({nog})}};"
                    )
                grain_lines.extend(
                    [
                        'Tp1[] = Point "*";',
                        "For i In {#Tp[]+1 : #Tp1[] - 1}",
                        "  Line(i)={i, i + 1};",
                        "EndFor",
                        "Line(#Tp1[])={#Tp1[], #Tp[]+1};",
                        "Line Loop(1+n+1)={#Tp[]+1: #Tp1[]};",
                        "n = n+1;",
                    ]
                )

    template_path = pat / f"templates/grid/{mode}.mako"
    geo_path = fol / "mesh.geo"

    mytemplate = Template(filename=str(template_path))
    if mode == "image":
        point_lines_str = "\n".join(point_lines)
        bdn_lines_str = "\n".join(bdn_lines)
    else:
        point_lines_str = None
        bdn_lines_str = None
    if mode == "device":
        point_left_lines_str = "\n".join(point_left_lines)
        point_right_lines_str = "\n".join(point_right_lines)
    else:
        point_left_lines_str = None
        point_right_lines_str = None
    grain_lines_str = "\n".join(grain_lines)
    filledtemplate = mytemplate.render(
        imL=imL,
        imH=imH,
        length=cfg.length,
        width=cfg.width,
        thickness=cfg.thickness,
        meshSize=cfg.meshSize,
        channelWidth=cfg.channelWidth,
        inlet=inlet,
        outlet=outlet,
        point_lines=point_lines_str,
        point_left_lines=point_left_lines_str,
        point_right_lines=point_right_lines_str,
        grain_lines=grain_lines_str,
        bdn_lines=bdn_lines_str,
    )

    with open(geo_path, "w", encoding="utf8") as file:
        file.write(filledtemplate)
    subprocess.run([gmsh, str(geo_path), "-3"], check=True)


def copy_and_replace(src: Path, dst: Path, replacements: dict[str, Any]) -> None:
    """Function to edit the OpenFOAM files"""
    text = src.read_text(encoding="utf8")
    for key, value in replacements.items():
        text = text.replace(key, str(value))
    dst.write_text(text, encoding="utf8")


def run_stokes(cfg: PymmConfig, fol: Path, pat: Path) -> None:
    """Function to write the openFOAM files to run the Navier-Stokes flow simulations"""
    template_base = f"{pat}/templates/OpenFOAM/flowStokes"
    flow_path = fol / "OpenFOAM/flowStokes"
    vtk_target = fol / "VTK_flowStokes"

    fol.mkdir(parents=True, exist_ok=True)
    (fol / "OpenFOAM").mkdir(parents=True, exist_ok=True)

    for name in ["OpenFOAM/flowStokes", "VTK_flowStokes"]:
        path = fol / name
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    for name in ["0", "constant", "system"]:
        (flow_path / name).mkdir(parents=True, exist_ok=True)

    for file_name in [
        Path("0/U"),
        Path("constant/momentumTransport"),
        Path("system/fvSchemes"),
    ]:
        shutil.copy2(template_base / file_name, flow_path / file_name)
    where = Path("0/p")
    copy_and_replace(
        template_base / where,
        flow_path / where,
        {
            "@inletValue@": cfg.inletValue,
        },
    )
    where = Path("constant/physicalProperties")
    copy_and_replace(
        template_base / where,
        flow_path / where,
        {
            "@viscosity@": cfg.viscosity,
        },
    )
    where = Path("system/controlDict")
    copy_and_replace(
        template_base / where,
        flow_path / where,
        {
            "@iterationsMax@": cfg.iterationsMax,
        },
    )
    where = Path("system/fvSolution")
    copy_and_replace(
        template_base / where,
        flow_path / where,
        {
            "@pressureConv@": cfg.pressureConv,
            "@velocityConv@": cfg.velocityConv,
        },
    )

    shutil.copy2(fol / "mesh.msh", flow_path)

    subprocess.run(["gmshToFoam", "mesh.msh"], cwd=flow_path, check=True)

    boundary_path = flow_path / "constant/polyMesh/boundary"
    lines = boundary_path.read_text(encoding="utf8").splitlines()
    lines[20] = "type      empty;"
    boundary_path.write_text("\n".join(lines) + "\n", encoding="utf8")

    # Running the steady-state flow simulation
    subprocess.run(
        ["foamRun", "-solver", "incompressibleFluid"], cwd=flow_path, check=True
    )
    subprocess.run(["foamToVTK"], cwd=flow_path, check=True)

    vtk_source = flow_path / "VTK"
    for item in vtk_source.iterdir():
        target = vtk_target / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy(item, target)


def run_tracer(cfg: PymmConfig, fol: Path, pat: Path) -> None:
    """Function to write the openFOAM files to run the Tracer flow simulations"""
    template_base = f"{pat}/templates/OpenFOAM/tracerTransport"
    tracer_path = fol / "OpenFOAM/tracerTransport"
    flow_stokes_path = fol / "OpenFOAM/flowStokes"

    for name in ["VTK_tracerTransport", "OpenFOAM/tracerTransport"]:
        path_obj = fol / name
        if path_obj.exists():
            shutil.rmtree(path_obj)
        path_obj.mkdir(parents=True, exist_ok=True)

    for name in ["0", "constant", "system"]:
        (tracer_path / name).mkdir(parents=True, exist_ok=True)

    for file_name in [
        Path("0/T"),
        Path("constant/fvConstraints"),
        Path("constant/momentumTransport"),
        Path("system/fvSchemes"),
        Path("system/fvSolution"),
        Path("system/topoSetDict"),
    ]:
        shutil.copy2(template_base / file_name, tracer_path / file_name)
    where = Path("constant/physicalProperties")
    copy_and_replace(
        template_base / where,
        tracer_path / where,
        {
            "@viscosity@": cfg.viscosity,
        },
    )
    where = Path("system/controlDict")
    copy_and_replace(
        template_base / where,
        tracer_path / where,
        {
            "@tracerTime@": cfg.tracerTime,
            "@tracerStep@": cfg.tracerStep,
            "@tracerWrite@": cfg.tracerWrite,
            "@diffusion@": cfg.diffusion,
        },
    )

    folders = [path for path in flow_stokes_path.iterdir() if path.is_dir()]
    latest_folder = max(folders, key=lambda path: path.stat().st_ctime)
    folders.remove(latest_folder)
    latest_folder = max(folders, key=lambda path: path.stat().st_ctime)

    shutil.copy2(latest_folder / "U", tracer_path / "0/")
    shutil.copy2(latest_folder / "p", tracer_path / "0/")
    shutil.copytree(
        flow_stokes_path / "constant/polyMesh",
        tracer_path / "constant/polyMesh",
        dirs_exist_ok=True,
    )
    subprocess.run(["topoSet"], cwd=tracer_path, check=True)

    # Running the simulation of tracer transport
    subprocess.run(["foamRun"], cwd=tracer_path, check=True)
    subprocess.run(["foamToVTK"], cwd=tracer_path, check=True)
    vtk_source = tracer_path / "VTK"
    for item in vtk_source.iterdir():
        target = fol / "VTK_tracerTransport" / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy(item, target)


# {
# Copyright 2022-2026, NORCE Research AS, Computational
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
