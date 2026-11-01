"""该脚本用于将NEP格式的EXYZ数据集分成训练集和测试集。

用法：python split_nep_data.py [filename]
"""

import random
import sys

from pynep.io import dump_nep, load_nep


def main():

    filename = sys.argv[1]
    train_ratio = 1.0  # 训练集比例
    rand = True  # 是否随机打乱数据集

    # 加载NEP数据集
    train_data = load_nep(filename, ftype="exyz")

    # 创建帧索引列表
    nframes = list(range(len(train_data)))

    # 随机打乱帧索引
    if rand:
        random.shuffle(nframes)

    # 计算训练集和测试集的帧索引
    train_frame = nframes[: int(len(train_data) * train_ratio)]
    test_frame = nframes[int(len(train_data) * train_ratio) :]

    # 导出训练集
    dump_nep("./train.xyz", [train_data[i] for i in train_frame], ftype="exyz")
    print(f"训练集已保存为: train.xyz, 包含 {len(train_frame)} 帧")

    # 导出测试集
    dump_nep("./test.xyz", [train_data[i] for i in test_frame], ftype="exyz")
    print(f"测试集已保存为: test.xyz, 包含 {len(test_frame)} 帧")


if __name__ == "__main__":
    main()
