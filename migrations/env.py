import os
from glob import glob

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from common.model import ModelBase
from config import CONFIG

# 只有完整导入了各个模块的定义才能在ModelBase.metadata获取完整数据
for file in glob(os.getcwd() + "/modules/*/models.py"):
    module = file.split(os.sep)[-2]
    # 动态创建并执行导入表达式
    exec(f"from modules.{module}.models import *")

config = context.config

# alembic不支持doris，因此这里需要替换成mysql
config.set_main_option("sqlalchemy.url", CONFIG.db_uri.replace("doris+", "mysql+"))
target_metadata = ModelBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
