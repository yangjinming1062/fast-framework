![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0+-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-v2.0+-green)

<br/>
<h1 align="center">
FastAPI后端项目框架
</h1>
<h4 align="center">专注于你的业务逻辑.</h4>
<br/>

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

## 构建镜像

```
docker build -t {image-name}:latest .
```

## 数据迁移
见[init.sh](data%2Fmigrate%2Finit.sh)

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
※ **允许同层调用，允许同层调用任意更低层级的代码，严谨调用更高层级的代码**

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

# 📚 使用帮助

本节主要针对基础功能代码的使用进行示例展示

- [common](common)：
  - [api.py](common%2Fapi.py)：用于API接口，主要使用场景是添加接口路由：
    ```
    from common.api import *  # api中几乎都是需要的东西（不需要的导入了也不会产生影响，因此建议直接*导入全部）
    from modules.{业务模块}.models import *
    from modules.{业务模块}.schemas import *
    
    router = get_router()  # router这个名字不能变，因为自动注册接口就是按照这个名字来处理的
    ```
  - [command.py](common%2Fcommand.py)：如果需要实现后台任务（与API服务并行），则需要在业务模块的command.py中按照下面的方式实现自定义的Command类：
    ```
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
  - [model.py](common%2Fmodel.py)：如果需要定于数据库的ORM模型，则需要在业务模块的models.py中按照下面的方式定义：
    ```
    from .enums import *
    from common.model import *


    class Demo(ModelBase, ModelTimeColumns):
        __tablename__ = "demo"

        type: Mapped[DemoTypeEnum]
        ...

    ```
  - [schema.py](common%2Fschema.py)：业务模块的schema.py中按照下面的方式定义：
    ```
    from .enums import *
    from common.schema import *


    class DemoSchema(SchemaBase):
        id: str
        created_at: datetime
        updated_at: datetime
        type: DemoTypeEnum
    ```

- [components](components)：components和common不同，将子内容统一进行了汇总，因此各个使用的地方直接`from components import *`即可。下面对components提供的主要功能进行介绍：
  - `logger`：本质就是loguru的logger，但是如果改用其他的日志记录库呢，调用端可以无感切换只改这里一个地方即可，因此从components中直接导入logger。同时也对格式和位置等进行了统一的配置。
    ```
    from components import *

    logger.info("hello world")
    ```
  - `DatabaseManager`： 统一实现数据库的连接创建、关闭、提交回滚等逻辑
    ```
    import json
    from components import *
  
    with DatabaseManager() as db:
        # 查询
        result = db.scalar(select(Demo).where(Demo.id == xxx))
        # 新增
        demo = Demo(type=DemoTypeEnum.A)
        db.add(demo)
        # 更新
        demo.type = DemoTypeEnum.B
        db.commit()
        # 删除
        db.delete(demo)
        # db.commit() 默认在退出上下文的时候自动进行提交，因此不需要手动commit，如果在过程中需要提交数据也是可以随时提交的
    ```
  - `generate_key`: ID生成，除了随机id也可以根据输入的内容每次都生成相同的id
    ```
    from components import *
    
    generate_key()  # '5c874da8b177b613fa872e9c'
    generate_key()  # 'a3454ad598b4c53393614c02'
    generate_key('abc')  # '0fc55f5588d4d4fed43e64a8'
    assert generate_key('abc', 123) == '39fb5e13879b5430df95d870'
    generate_key(key_len=12)  # 'ef0685eadd03'
    generate_key(key_len=36)  # '3d4accaa58a84c25a0c2d599c83c3dee'
    generate_key(need_uuid=True)  # UUID('d855df18-e925-4aa6-8941-49ce2eb7b9dc')
    ```
  - `KafkaManager`：统一实现kafka的生成和消费操作
    - 生产数据：
      ```
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
      ```
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
      consumer = KafkaConsumer("topic_name")
      for data in KafkaManager.consume(consumer=consumer):
          assert isinstance(data, dict)
      
      # 5.非JSON格式的数据消费：默认是把数据当作JSON格式进行消费并转换成python的数据类型，但是也支持非JSON格式
      for data in KafkaManager.consume("topic_name", need_load=False):
          assert isinstance(data, bytes)
      ```
  - `RedisManager`：本质上就是用来获取Redis的Client，但是可以不用关心具体的连接参数是什么，同时针对“对象”格式简单进行了封装。
    ```
    from components import *
    
    redis = RedisManager.get_client()
    redis.incrby("key", 1)
    redis.get("key")
    
    # 也可以指定db
    redis1 = RedisManager.get_client(1)
    
    # 如果需要存取对象的话可以直接用类方法
    RedisManager.set_object("key", {"a": 1})
    RedisManager.set_object("key1", {"a": 1}, ex=60)  # 设置过期时间
    RedisManager.get_object("key") == {"a": 1}
    RedisManager.get_object("unexist_key", 100) == 100  # 可以指定key不存在时的默认值
    ```
  - `SecretManager`：加密解密相关的操作，可以对一些敏感信息进行加密，比如密码、密钥等。
    ```
    from components import *
    
    # 加密
    secret = SecretManager.encrypt("123456")
    assert secret != "123456"  # 加密后的内容取决于密钥是什么，因此生产环境不能使用随机密钥
    # 解密
    assert SecretManager.decrypt(secret) == "123456"
    ```
  - 其他诸如`bytes_to_str`，`str_to_bytes`等不再一一追朔，每个方法都有对应的注释说明。
