"""baseline: 1-bosqich sxemasi (barcha jadvallar)

Bu migratsiya joriy modellardan jadvallarni yaratadi. Keyingi barcha o'zgarishlar
avtomatik generatsiya qilinadi:  alembic revision --autogenerate -m "nima o'zgardi"
"""
from alembic import op

from app.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
