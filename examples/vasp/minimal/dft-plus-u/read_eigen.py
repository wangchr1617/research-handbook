"""读取本例 XML 的 k 点、本征值及实际生效参数，能量单位 eV。"""

import xml.etree.ElementTree as ET

import numpy as np


def read_eigen(stage):
    root = ET.parse(f"{stage}/vasprun.xml").getroot()
    kpoints = np.array(
        [
            [float(v) for v in row.text.split()]
            for row in root.findall("kpoints/varray[@name='kpointlist']/v")
        ]
    )
    sets = root.findall("calculation")[-1].findall("eigenvalues/array/set/set")
    values = np.array(
        [
            [
                [[float(v) for v in row.text.split()] for row in point.findall("r")]
                for point in spin.findall("set")
            ]
            for spin in sets
        ]
    )
    parameters = {
        node.attrib["name"]: (node.text or "").strip()
        for node in root.findall(".//parameters//i")
    }
    return kpoints, values, parameters


def sampled_gap(values):
    eigen = values[:, :, :, 0]
    occup = values[:, :, :, 1]
    occupied = eigen[occup > 0.5]
    empty = eigen[occup <= 0.5]
    return max(0.0, float(empty.min() - occupied.max()))
