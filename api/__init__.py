from glob import glob

from .common import *

for name in glob(os.path.dirname(__file__) + '/*/*.??'):
    if os.path.isfile(name) and not name.endswith('__.py'):
        tmp = name.split(os.sep)[-3:]
        module = '.'.join(tmp)[:-3]  # [:-3]是去掉文件的后缀名
        name = '_'.join(tmp)[:-3]
        expression = f'from {module} import router as {name}_router'
        exec(expression)

# 用于在创建app时动态注册蓝图
ROUTERS = [module for name, module in globals().items() if name.endswith('_router') and isinstance(module, APIRouter)]
