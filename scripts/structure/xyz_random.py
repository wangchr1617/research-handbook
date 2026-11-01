"""从扩展 XYZ 文件随机抽取结构帧。

用法：python xyz_random.py
"""

import random


def read_exyz_structure(file):
    structures = []
    current_structure = []
    atom_count = 0
    read_atoms = 0
    for line in file:
        if read_atoms == 0:
            try:
                atom_count = int(line.split()[0])
            except ValueError:
                continue
            current_structure = [line]
            read_atoms = atom_count + 1
        else:
            current_structure.append(line)
            read_atoms -= 1
            if read_atoms == 0:
                structures.append(current_structure)
    return structures


def write_exyz_structure(file, structure):
    for line in structure:
        file.write(line)


def extract_and_write_random_structures(input_filename, output_filename, n):
    with open(input_filename, "r") as input_file:
        structures = read_exyz_structure(input_file)
    selected_structures = random.sample(structures, min(n, len(structures)))
    with open(output_filename, "w") as output_file:
        for structure in selected_structures:
            write_exyz_structure(output_file, structure)


def main():

    input_filename = "./train.xyz"  # 输入文件路径
    output_filename = "./output.exyz"  # 输出文件路径
    number_of_structures = 10000  # 抽取结构数

    extract_and_write_random_structures(
        input_filename, output_filename, number_of_structures
    )


if __name__ == "__main__":
    main()
