![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-v2.0+-green)

<br/>
<h1 align="center">
FastAPI后端项目框架
</h1>
<h4 align="center">专注于你的业务逻辑.</h4>
<br/>

# 目录

- [⚡ 快速开始](#-快速开始)
- [🔧 环境配置](#-环境配置)
- [🚀 部署指南](#-部署指南)
- [💻 开发规范](#-开发规范)
- [📄 结构介绍](#-结构介绍)
- [📚 使用帮助](#-使用帮助)

# 💡 功能特点

- 容器化：提供Docker及docker-compose文件，按需修改其中的参数即可使用（不改也能用）
- 轻量化：依赖的库尽可能的少
- 分层归类：实体、枚举、业务逻辑条理清晰
- 封装：接口的请求响应等常规内容均进行了统一的封装，专注于实现业务逻辑本身就好

# ⚡ 快速开始

## 本地开发

1. `pip install -r requirements.txt` 安装依赖
2. 安装pre-commit，`pip install pre-commit`
3. 运行`pre-commit install`安装pre-commit钩子
4. 运行`pre-commit run -a`初始化repos
5. 运行main.py文件启动API服务

## 数据迁移

[versions](migrations%2Fversions)目录下存放着当前版本的数据库迁移脚本，执行`alembic upgrade head`命令进行数据库迁移。

代码中调整了model的定义后使用`alembic revision --autogenerate`重新生成迁移脚本。
**autogenerate只能按照[script.py.mako](migrations%2Fscript.py.mako)模板生成迁移脚本，具体的{version}_upgrade.sql/{version}_downgrade.sql需要根据变更提供**

### 版本号管理:

*建议每个版本仅保留一个版本对应的迁移脚本，多次bugfix的情况下在最终确定版本时生成一个当前版本最终的迁移脚本。*
具体版本号命名规则按需调整，以下仅为示例：其中v1.0为前一次的发布版本，v1.1为当前版本。过程中的~~v1.0.1~~ -> ~~v1.0.2~~ -> ~~v1.0.3~~在最终发布v1.1进行整合并删除。
v1.0 -> ~~v1.0.1~~ -> ~~v1.0.2~~ -> ~~v1.0.3~~ -> v1.1 = v1.0 -> v1.1

# 🔧 环境配置

## 配置文件说明

项目使用多种配置文件管理系统配置，单一配置文件中可以只提供部分参数，比如只想修改数据库连接地址则dev.env只提供数据库参数即可，不必给出全部所有的参数

## 环境变量优先级

配置加载优先级从高到低：

1. 环境变量
2. dev.env
3. .env
4. config.yaml
5. 参数默认值

# 🚀 部署指南

## Docker部署

1. 构建镜像

```bash
docker build -t {image-name}:latest .
```

2. 运行容器

```bash
docker run -d \
  --name api-server \
  -p 8000:8000 \
  -v /path/to/config.yaml:/app/config.yaml \
  {image-name}:latest
```

3. 使用Docker Compose（推荐）

```yaml
services:
  api-server:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml
```

# 💻 开发规范

## Git分支管理

- `main`: 主分支,按版本号进行合并
- `dev/*`: 各种开发中的分支

## 代码风格

项目使用pre-commit进行代码风格检查，主要使用black进行Python代码格式化

# 📄 结构介绍

## 架构设计

<table>
  <tr>
    <th>基础组件</th>
    <th>业务逻辑</th>
    <th>对外接口</th>
    <th>程序入口</th>
  </tr>
    <tr>
    <td>common</td>
    <td rowspan="3">modules</td>
    <td rowspan="3">api</td>
    <td>main.py</td>
  </tr>
  <tr>
    <td>components</td>
    <td>command.py</td>
  </tr>
  <tr>
    <td>config</td>
  </tr>
</table>

*系统主要由上述五个部分+两个入口点组成，表格越往右层级越高*

### 调用原则
※ **允许同层调用，允许同层调用任意更低层级的代码，严禁调用更高层级的代码**

### 组件说明
PS: *本部分按照使用的先后顺序进行排序，不按照字母顺序进行排序*
- [config](config): 代码中应该严格杜绝硬编码的行为，因此把参数都定义在config中。config的导出限制中限定了仅导出CONFIG和CONSTANTS两个实例
  - CONFIG：包含可以通过环境变量在启动程序时修改的参数，因为在类中显著的标明属性和类型，因此不要再但是参数多了的时候不知道都有哪些参数的问题。
  - CONSTANTS：包含一些业务无关的常量值，比如说时间类型序列化时的格式等。
- [components](components): components是对业务无关的一些处理逻辑的封装，如果是高度聚合的操作就封装成Manager类，比如对kafka的操作就封装到KafkaManager类中，如果是单独的函数逻辑就可以都放到functions中。另外components的__init__中对分散在各个文件中的封装组件进行了汇总同时限制了导出的内容，这样使用的时候只需要从components导入*或者特定内容即可而无需知道是在components的functions中还是redis中。
- [common](common): common也是对业务无关的封装，但是和components不同，common中主要封装的是各种“定义”或者说基类，同时因为common中的文件是按照应用场景的类型划分的，因此也就没有在__init__中对分散在各个文件中的定义进行汇总。
- [modules](modules): 上面的所有封装都强调了一点就是“业务无关”性，因此他们是基础组件。于此相对的，系统中包含众多业务逻辑，这些业务逻辑也都可以按照功能模型进行拆分，因此modules中存放的就是业务逻辑模块。modules下应该包含的是各个业务模块，因此具体叫什么就因业务逻辑而定，但是每个业务逻辑模块中包含的文件定义应该有一定的标准，下面还是按照应用的先后顺序进行说明：
  - [可选]constants.py: 上面提到了CONSTANTS中都是业务逻辑无关的常量，那如果我需要定义一些跟业务逻辑相关的呢？就比如我有一个消息队列的名称，代码中严禁硬编码的话写到哪呢，当然就是写到自己模块的constants文件中。
  - [可选]enums.py: 在进行数据结构设计的时候可能会存在一下枚举类型，这些枚举类型是跟业务相关的，就比如说用户类型枚举就应该放到用户模块中进行定义。
  - [可选]models.py: 数据库模型定义，如果当前业务逻辑涉及到跟数据库交互的话，业务所属的model应该定义在这里。
  - [可选]schemas.py: 说可选也不算是，除非当前业务模块不对外提供API接口或者虽然提供接口但是都是简单的数据结构，不然跟API相关的数据结构定义都在这里。如果跟接口强相关的建议就是xxxRequest\xxxResponse这样明确表示用于哪个接口，如果跟接口不强相关则应该是xxxSchema表明这是一个数据结构的定义以免跟model中的model定义混淆。
  - [可选]controller.py: 业务逻辑的封装，建议就叫做xxxController把相关逻辑都封装到一个类中，导出使用也方便。（PS：之所以可选是因为建议封装的是较为繁琐或者说可能被多个接口共用到的逻辑，如果是跟特定接口强相关的查询之类的逻辑还是直接写在特定的API中比较好）。
  - [可选]command.py: 如果当前业务模块需要有一些跟API服务并行的后台服务则需要定义该文件，其中需要实现一个使用CommandBase元类的子类（使用元类后进行自动注册）。
  - [可选]其他按需定义的模块文件

## 入口点

项目一共提供两种入口点，分别是：

- [main.py](main.py): 启动API服务，同时对API接口的错误响应进行指定格式的转化处理。
- [command.py](command.py): 通过终端执行的其他后台任务。PS:command文件不需要再进行修改，业务模块自己的命令只需要按照上面的要求进行实现command在启动的时候就会自动注册并发现。

之所以这样设计是考虑到除了提供API服务外还可能存在一些后台任务，比如持续处理数据之类的。

### Q & A
Q: 为什么不把main.py和command.py合并成一个文件？
A: 主要是考虑到二者的根本结构和目的都不一样，单独拆分开也能更好的解耦合。debug的时候启动main也不需要提供什么而外的参数。

## API接口

API接口的设计主要遵循RESTful API设计规范，同时对一些高度同质化的内容进行了封装处理。
下面对API模块的特定、实现的封装等进行说明：
- 自动注册：api目录下已经预先放置了[v1](api%2Fv1)目录,编写接口时只需要在目标文件夹中新增python文件即可在启动API服务时自动完成接口路径的补全：接口路径规则:
  /api/{v1}/{业务模块}/{接口定义的子path}。
- 统一分页：分页类的接口入参和出参定义应该分别继承自`PaginateRequest`和`PaginateResponse`,然后查询的时候只需要构建好查询数据的SQL语句按照参数要求调用`paginate_query`方法即可（paginate_query对数据的分页、导出文件，总数查询等高度同质化的内容都做了封装）。
- 错误处理：因为需要对错误响应进行统一的格式化，因此使用了`APIException`来进行错误抛出，同时为了避免硬编码的出现引入了`APICode`类来定义错误码和错误信息。
- 状态码：目前主要有以下几种状态码，分别对应不同的场景：
  - 200：数据查询成功时（例如：分页、详情、图标等）
  - 201：创建数据类接口成功时（例如：新建数据、创造任务等）
  - 204：操作类接口无需返回数据时（例如：删除、编辑）
  - 400：明显的客户端错误（例如：格式错误的请求语法，太大的大小，无效的请求消息或欺骗性路由请求）
  - 404：数据不存在
  - 403：禁止操作
  - 422：入参不正确
  - 500：异同异常

# 📚 使用帮助

## 公共代码封装

### API接口

[api.py](common%2Fapi.py)：用于API接口，主要使用场景是添加接口路由

```python
from common.api import *  # api中几乎都是需要的东西（不需要的导入了也不会产生影响，因此建议直接*导入全部）
from modules.{业务模块}.models import *
from modules.{业务模块}.schemas import *

router = get_router()  # router这个变量名字不能改，因为自动注册接口就是按照这个名字来处理的

# 注册类接口标准：新增数据实体成功响应新增数据的id，返回201状态码
@router.post("", status_code=201)
async def create_demo(request: DemoSchema):
    """
    示例：新增数据
    """
    ...


# 删除数据标准：可接收复数的params参数传递id，删除成功时无响应数据返回204状态码
@router.delete("", status_code=204)
async def delete_demo(request: list[str]):
    """
    示例：删除数据
    """
    ...



# 编辑数据标准：接收数据实体的Schema（put应该是完整覆盖，只更新部分应该用patch），如果更新成功无响应数据返回204状态码
@router.put("", status_code=204)
async def edit_demo(request: DemoSchema):
    """
    示例：修改数据
    """
    ...


# 分页查询标准：paginate_query统一封装了下载及分页支持，需要做的是按照需求基于分页的入参和响应Schema派生子Schema定义，并在接口处生成查询语句，处理过滤条件
@router.post("/demos")
async def get_demo_list(request: DemosRequest) -> DemosResponse:
    """
    示例：查询列表
    """
    # 生成查询语句
    stmt = select(Demo.id, Demo.created_at)
    # 添加过滤条件
    if query := request.query:
        # 以下三种方式等价
        # 1. 使用集成的add_filters，好处是可以一次性添加上所有的过滤条件
        stmt = add_filters(stmt, query, {Demo.created_at: FilterTypeEnum.Datetime})
        # 2. 使用get_condition, 好处同类型的参数处理进行了封装，且比add_filters更灵活可以指定参数应用的位置（where、having）
        if condition := get_condition(Demo.created_at, query.created_at, FilterTypeEnum.Datetime):
            stmt = stmt.where(condition)
        # 3. 直接使用SQLAlchemy的SQL语法进行操作，操作最灵活，但不易统一维护
        if query.created_at:
            stmt = stmt.where(Demo.created_at.between(query.created_at.start, query.created_at.end))
    # 统一执行查询
    return paginate_query(stmt, request, DemosResponse)


# 查询详情
@router.get("/{id}")
async def get_demo_detail(id: str) -> DemoSchema:
    """
    示例：查询详情
    """
    ...
```

### 命令调用

[command.py](##common%2Fcommand.py)：如果需要实现后台任务（与API服务并行），则需要在业务模块的command.py中按照下面的方式实现自定义的Command类

```python
from common.command import CommandBase

class DemoCommand(metaclass=CommandBase):
    name = "demo"  # 命令名称，必须唯一，自动注册命令时会使用这个名字，同时这个也是python command.py {module} xxx 中的module的参数值
  
    @staticmethod
    def add_parser(parser):
        parser.add_argument(
            "--username",
            default="admin",
            help="参数说明",
        )
  
    @staticmethod
    def run(params):
        assert "username" in params
```

### ORM模型定义

[model.py](common%2Fmodel.py)：如果需要定于数据库的ORM模型，则需要在业务模块的models.py中按照下面的方式定义

```python
from .enums import *
from common.model import *


class Demo(ModelBase, ModelTimeColumns):
    __tablename__ = "demo"

    type: Mapped[DemoTypeEnum]
    ...

```

### 业务模型定义

[schema.py](common%2Fschema.py)：业务模块的schema.py中按照下面的方式定义

```python
from .enums import *
from common.schema import *


class DemoSchema(SchemaBase):
    id: str
    created_at: datetime
    updated_at: datetime
    type: DemoTypeEnum
```

## 组件使用示例

[components](components)：components和common不同，将子内容统一进行了汇总，因此各个使用的地方直接`from components import *`即可。

### 日志记录

本质就是loguru的logger，但是如果改用其他的日志记录库呢，调用端可以无感切换只改这里一个地方即可，因此从components中直接导入logger。同时也对格式和位置等进行了统一的配置。

```python
from components import *

logger.info("hello world")
```

### Kafka

- 生产数据：

```python
from components import *

# 1.生成单条数据
KafkaManager.produce(
      "topic_name",
      {
          "id": generate_key(),
          "value": 0,
      },
  )

# 2.批量生产也是欢迎的，PS:批量生产也不需要关心队列的长度，会自动进行分批发送，所以有很长的数据就一股脑扔进去也没关系
KafkaManager.produce(
      "topic_name",
      [{"id": generate_key()} for i in range(10000)],
  )
```

- 消费数据：`KafkaManager.consume`是一个生成器，可以不断的从kafka中消费数据，除非触发了异常。

```python
from components import *

# 1.消费单一Topic的数据
for data in KafkaManager.consume("topic_name"):
    assert isinstance(data, dict)

# 2.同时消费多个Topic也是可以的
for data in KafkaManager.consume("topic_name1", "topic_name2"):
    assert isinstance(data, dict)

# 3.批量消费数据: 通过limit参数可以指定每次消费的数据量，如果不指定默认则是上面的单条消费
for data in KafkaManager.consume("topic_name", limit=1000):
    assert isinstance(data, list)
    assert len(data) == 1000
  
# 4.提前创建好consumer：consumer参数默认是None，此时会根据topic_name自动创建consumer，如果指定consumer则使用提前创建好的consumer
# PS：自动创建的consumer在异常发生时除了会中断生成器也会自动关闭和取消订阅，但是如果手动创建了consumer则不会自动关闭，需要手动关闭
consumer = KafkaManager.get_consumer("topic_name")
for data in KafkaManager.consume(consumer=consumer):
    assert isinstance(data, dict)

# 5.非JSON格式的数据消费：默认是把数据当作JSON格式进行消费并转换成python的数据类型，但是也支持非JSON格式
for data in KafkaManager.consume("topic_name", need_load=False):
    assert isinstance(data, bytes)
```

### Redis

```python
from components import *

# 推荐一个业务模块全大写定义一个全局的客户端实例
REDIS = RedisManager.get_client()
REDIS.incrby("key", 1)
REDIS.get("key")

# 也可以指定db
REDIS1 = RedisManager.get_client(1)

# 如果需要存取对象的话可以直接用类方法
RedisManager.set_object("key", {"a": 1})
RedisManager.set_object("key1", {"a": 1}, ex=60)  # 设置过期时间
RedisManager.get_object("key") == {"a": 1}
RedisManager.get_object("unexist_key", 100) == 100  # 可以指定key不存在时的默认值
```

### 数据库

```python
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

from components import *
from modules.auth.models import *

# region 增
with DatabaseManager() as db:
    
    # 使用ORM的方式
    item = User(username=0)
    db.add(item)
    db.flush()  # 如果需要自增id这种提交后生成的信息又不想提交可以先flush
    # db.commit() 默认在退出上下文的时候自动进行提交，因此不需要手动commit，如果在过程中需要提交数据也是可以随时提交的
    # tips: # db.add() * N 之后会在flush或者commit进行批量插入，不用再单独进行bulk_save_objects了
    
    # 使用sql的方式
    stmt = insert(User).values(username='admin')
    db.execute(stmt)
# endregion

# region 查
with DatabaseManager() as db:
    # 有唯一主键使用唯一主键获取数据实例
    item = db.get(User, 'user-id')
    assert isinstance(item, User)
    
    # 用各种where条件构建sql语句查实例
    stmt = select(User).where(User.id == 'user-id')
    item = db.scalar(stmt)  # tips：查询数据的时候db.scalar(stmt)等效于db.execute(stmt).scalar()，从简洁的角度出发建议使用前者
    assert isinstance(item, User)
    
    # 2.0版本前ORM的查询方式，不推荐
    users = db.query(User).filter_by(phone=0).all()
    assert isinstance(users, list)
    
    # 推荐使用stmt的方式
    stmt = select(User).where(User.phone == 0)
    users = db.scalars(stmt).all()  # tips: 和scalar一样db.scalars(stmt).all()等效于db.execute(stmt).scalars().all()
    assert isinstance(users, list)
    # tips: 如果查询出的数据需要遍历进行处理更好的方式是下面这种直接迭代db.scalars(stmt)，可以减少一次遍历（all的本质就是先把数据都拿出来）
    for item in db.scalars(stmt):
        ...
    
    # 只查询部分列的值
    stmt = select(User.id, User.username)
    data = db.execute(stmt).all()  # 这种查询中有多个列的时候就不能scalar或scalars，因为scalar就只取第一列的值
    # 查询的每一行是一个tuple
    for user_id, username in db.execute(stmt):
        ...
# endregion

# region 删
with DatabaseManager() as db:
    # 使用ORM的方式：需要先查出来一个实例对象
    item = db.get(User, 'user-id')
    db.delete(item)  # tips: 这种方式的缺点就是一下只能删一条数据，适合单条数据编辑的场景，优点是可以同时删除掉级联的子数据（如果定义了外键关联的话）
    
    # 使用sql语句的方式: 便于一次性进行批量删除
    stmt = delete(User).where(User.id == 'user-id')
    db.execute(stmt)
# endregion

# region 改
with DatabaseManager() as db:
    # 使用ORM的方式：需要先查出来一个实例对象
    item = db.get(User, 'user-id')
    item.username = 'new'  # 没错，就直接赋值就可以了，提交就变。tips: 需要注意的就是在一般查询场景下因为orm的这种特性尽量就不要对查出来的实例进行赋值操作了，可以对dump出来的json数据进行编辑（如果不想修改的话）
    db.flush()
    
    # 使用sql语句的方式
    stmt = update(User).where(User.id == 'user-id').values(username='new')
    db.execute(stmt)
# endregion

```

### 加密解密

`SecretManager`：加密解密相关的操作，可以对一些敏感信息进行加密，比如密码、密钥等。

```python
from components import *

# 加密
secret = SecretManager.encrypt("123456")
assert secret != "123456"  # 加密后的内容取决于密钥是什么，因此生产环境不能使用随机密钥
# 解密
assert SecretManager.decrypt(secret) == "123456"
```
