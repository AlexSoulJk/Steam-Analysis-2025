"""update fields player.Friend & user.User

Revision ID: a0103b552f6e
Revises: ce8fc3fc1aad
Create Date: 2025-12-01 15:38:49.157998

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0103b552f6e'
down_revision: Union[str, Sequence[str], None] = 'ce8fc3fc1aad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if bind.engine.name == 'sqlite':
        # Шаг 1: Сначала добавим новые колонки
        with op.batch_alter_table('friends', recreate='auto') as batch_op:
            batch_op.add_column(sa.Column('user_steamid', sa.String(length=500), nullable=True))
            batch_op.add_column(sa.Column('friend_steamid', sa.String(length=500), nullable=True))

        # Шаг 2: Затем изменим friend_id (отдельным batch)
        with op.batch_alter_table('friends', recreate='auto') as batch_op:
            batch_op.alter_column('friend_id',
                                  existing_type=sa.INTEGER(),
                                  nullable=True)

        # Шаг 3: Изменяем users таблицу
        with op.batch_alter_table('users', recreate='auto') as batch_op:
            batch_op.alter_column('loccityid',
                                  existing_type=sa.VARCHAR(length=500),
                                  type_=sa.Integer(),
                                  existing_nullable=True)
    else:
        # Оригинальный код для других БД
        op.add_column('friends', sa.Column('user_steamid', sa.String(length=500), nullable=True))
        op.add_column('friends', sa.Column('friend_steamid', sa.String(length=500), nullable=True))
        op.alter_column('friends', 'friend_id',
                        existing_type=sa.INTEGER(),
                        nullable=True)
        op.alter_column('users', 'loccityid',
                        existing_type=sa.VARCHAR(length=500),
                        type_=sa.Integer(),
                        existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if bind.engine.name == 'sqlite':
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column('loccityid',
                                  existing_type=sa.Integer(),
                                  type_=sa.VARCHAR(length=500),
                                  existing_nullable=True)

        with op.batch_alter_table('friends') as batch_op:
            batch_op.alter_column('friend_id',
                                  existing_type=sa.INTEGER(),
                                  nullable=False)
            batch_op.drop_column('friend_steamid')
            batch_op.drop_column('user_steamid')
    else:
        op.alter_column('users', 'loccityid',
                        existing_type=sa.Integer(),
                        type_=sa.VARCHAR(length=500),
                        existing_nullable=True)
        op.alter_column('friends', 'friend_id',
                        existing_type=sa.INTEGER(),
                        nullable=False)
        op.drop_column('friends', 'friend_steamid')
        op.drop_column('friends', 'user_steamid')
