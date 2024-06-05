import argparse
import os
from glob import glob

from common.command import CommandBase

# 自动查找modules目录下的所有模块，并动态导入其中的命令（不导入则不会被注册到CommandBase的registry中）
for file in glob(os.path.dirname(__file__) + "/modules/*/command.py"):
    module = file.split(os.sep)[-2]
    # 动态创建并执行导入表达式
    exec(f"from modules.{module}.command import *")


def main():
    parser = argparse.ArgumentParser(description="终端命令行工具")
    # 添加子命令
    subparsers = parser.add_subparsers(dest="module")
    # 注册各个模块的命令参数
    for name, command in CommandBase.registry.items():
        command.add_parser(subparsers.add_parser(name))
    # 解析参数
    args = parser.parse_args()
    # 执行命令
    CommandBase.registry[args.module].run(args)


if __name__ == "__main__":
    main()
