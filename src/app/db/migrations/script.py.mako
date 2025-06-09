"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql  # For PostgreSQL-specific types (JSONB, UUID, etc.)
from sqlalchemy.sql import text  # For raw SQL queries
${imports if imports else ""}

# --- Revision identifiers ---
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels) if branch_labels else None}
depends_on = ${repr(depends_on) if depends_on else None}

def upgrade():
    """Upgrade database schema to this revision."""
    bind = op.get_bind()  # Optional: Get the DB connection for raw SQL
    ${upgrades if upgrades else "pass"}

def downgrade():
    """Downgrade database schema to the previous revision."""
    bind = op.get_bind()  # Optional: Get the DB connection for raw SQL
    ${downgrades if downgrades else "pass"}