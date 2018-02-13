"""empty message

Revision ID: 7eebb1004b2f
Revises:
Create Date: 2018-02-11 15:12:00.208326

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7eebb1004b2f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('deals', 'owner_id',
               existing_type=sa.VARCHAR(length=5),
               nullable=False)
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('deals', 'owner_id',
               existing_type=sa.VARCHAR(length=5),
               nullable=True)
    # ### end Alembic commands ###