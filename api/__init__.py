import os
from glob import glob

from .common import *

# 在当前目录下找所有实现接口的文件，具体的pattern根据实际情况调整，但至少应该保证深度一致
for name in glob(os.path.dirname(__file__) + "/v*/*.??"):
    # 判断是否是文件，并且不是以' __.py '结尾的文件(排除掉__init__.py)。
    if os.path.isfile(name) and not name.endswith("__.py"):
        # 将文件路径拆分为目录列表，-3还是-*取决于pattern的目录层深
        tmp = name.split(os.sep)[-3:]
        # 将这些目录连接起来形成模块名，[:-3]是去掉文件的后缀名
        module = ".".join(tmp)[:-3]
        # 用下划线连接目录以形成名称
        name = "_".join(tmp)[:-3]
        # 动态创建并执行导入表达式
        exec(f"from {module} import router as {name}_router")

# 用于在创建app时动态注册蓝图
ROUTERS = [module for name, module in locals().items() if name.endswith("_router") and isinstance(module, APIRouter)]
