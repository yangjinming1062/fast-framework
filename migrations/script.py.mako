"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}

"""
import os
from typing import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}
current_dir = os.path.dirname(os.path.realpath(__file__))


def operate_sql(sql_file: str):
    if os.path.exists(sql_file):
        with open(sql_file) as f:
            content = f.read()
        for statement in content.split(';'):
            if statement := statement.strip(' \n'):
                op.execute(statement)


def upgrade() -> None:
    operate_sql(f'{current_dir}/{revision}_upgrade.sql')


def downgrade() -> None:
    operate_sql(f'{current_dir}/{revision}_downgrade.sql')
