"""Drop index with constraint

Revision ID: ccfbe50ade1d
Revises: 9b18da156691
Create Date: 2025-12-09 22:51:12.283042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccfbe50ade1d'
down_revision: Union[str, Sequence[str], None] = '9b18da156691'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if bind.engine.name == 'sqlite':
        # Для SQLite используем batch mode
        with op.batch_alter_table('friends', recreate='auto') as batch_op:
            batch_op.drop_constraint('uq_friends_pair', type_='unique')
    else:
        # Для других БД (PostgreSQL, MySQL) оставляем оригинальный код
        op.drop_constraint(op.f('uq_friends_pair'), 'friends', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if bind.engine.name == 'sqlite':
        # Для SQLite используем batch mode
        with op.batch_alter_table('friends', recreate='auto') as batch_op:
            batch_op.create_unique_constraint('uq_friends_pair', ['user_id', 'friend_id'])
    else:
        # Для других БД оставляем оригинальный код
        op.create_unique_constraint(op.f('uq_friends_pair'), 'friends', ['user_id', 'friend_id'])
