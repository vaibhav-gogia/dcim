"""Insert data halls between data centers and racks without replacing inventory."""
from alembic import op
import sqlalchemy as sa

revision = "20261008_data_halls"
down_revision = "00df4e4d1497"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "data_halls",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("datacenter_id", sa.UUID(), sa.ForeignKey("datacenters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("datacenter_id", "name", name="uq_hall_name_per_dc"),
    )
    op.add_column("racks", sa.Column("data_hall_id", sa.UUID(), nullable=True))
    op.execute("INSERT INTO data_halls (datacenter_id, name) SELECT id, 'Hall 1' FROM datacenters")
    op.execute("UPDATE racks SET data_hall_id = data_halls.id FROM data_halls WHERE racks.datacenter_id = data_halls.datacenter_id")
    op.alter_column("racks", "data_hall_id", nullable=False)
    op.create_foreign_key("racks_data_hall_id_fkey", "racks", "data_halls", ["data_hall_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("uq_rack_name_per_dc", "racks", type_="unique")
    op.create_unique_constraint("uq_rack_name_per_hall", "racks", ["data_hall_id", "name"])
    op.drop_constraint("racks_datacenter_id_fkey", "racks", type_="foreignkey")
    op.drop_column("racks", "datacenter_id")


def downgrade():
    # Refuse to discard hall identity or merge conflicting rack names silently.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM data_halls GROUP BY datacenter_id HAVING count(*) > 1 LIMIT 1")).first():
        raise RuntimeError("Cannot remove the data-hall layer while a data center has multiple halls.")
    op.add_column("racks", sa.Column("datacenter_id", sa.UUID(), nullable=True))
    op.execute("UPDATE racks SET datacenter_id = data_halls.datacenter_id FROM data_halls WHERE racks.data_hall_id = data_halls.id")
    op.alter_column("racks", "datacenter_id", nullable=False)
    op.create_foreign_key("racks_datacenter_id_fkey", "racks", "datacenters", ["datacenter_id"], ["id"], ondelete="CASCADE")
    op.drop_constraint("uq_rack_name_per_hall", "racks", type_="unique")
    op.create_unique_constraint("uq_rack_name_per_dc", "racks", ["datacenter_id", "name"])
    op.drop_constraint("racks_data_hall_id_fkey", "racks", type_="foreignkey")
    op.drop_column("racks", "data_hall_id")
    op.drop_table("data_halls")
