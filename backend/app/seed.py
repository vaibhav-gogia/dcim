"""Populates one demo data center with racks, PDUs, and systems for local dev/demo.

Run with: python -m app.seed
"""

import asyncio
import random

from app.database import async_session_maker
from app.models.datacenter import DataCenter
from app.models.pdu import PDU
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.rack import Rack
from app.models.system import System

RACK_LAYOUT = [
    {"name": "R01", "pos_x": 0, "pos_y": 0},
    {"name": "R02", "pos_x": 1, "pos_y": 0},
    {"name": "R03", "pos_x": 2, "pos_y": 0},
    {"name": "R04", "pos_x": 0, "pos_y": 1},
    {"name": "R05", "pos_x": 1, "pos_y": 1},
]

SYSTEM_TYPES = ["server", "server", "server", "network", "storage"]
MANUFACTURERS = ["Dell", "HPE", "Supermicro", "Lenovo"]


async def seed() -> None:
    async with async_session_maker() as db:
        dc = DataCenter(name="DC-East-01", location="Markham, ON")
        db.add(dc)
        await db.flush()

        for rack_def in RACK_LAYOUT:
            rack = Rack(
                datacenter_id=dc.id,
                name=rack_def["name"],
                u_height=42,
                pos_x=rack_def["pos_x"],
                pos_y=rack_def["pos_y"],
            )
            db.add(rack)
            await db.flush()

            pdu_a = PDU(rack_id=rack.id, name=f"{rack.name}-PDU-A", outlet_count=24)
            pdu_b = PDU(rack_id=rack.id, name=f"{rack.name}-PDU-B", outlet_count=24)
            db.add_all([pdu_a, pdu_b])
            await db.flush()

            outlets_a = [PDUOutlet(pdu_id=pdu_a.id, outlet_number=n, state="on") for n in range(1, 25)]
            outlets_b = [PDUOutlet(pdu_id=pdu_b.id, outlet_number=n, state="on") for n in range(1, 25)]
            db.add_all(outlets_a + outlets_b)
            await db.flush()

            system_count = random.randint(6, 10)
            next_u = 2
            for i in range(system_count):
                if next_u > 40:
                    break
                u_height = random.choice([1, 1, 1, 2, 4])
                if next_u + u_height - 1 > 42:
                    break
                system = System(
                    rack_id=rack.id,
                    name=f"{rack.name.lower()}-sys{i + 1:02d}",
                    u_position=next_u,
                    u_height=u_height,
                    system_type=random.choice(SYSTEM_TYPES),
                    manufacturer=random.choice(MANUFACTURERS),
                    model="Gen10" if u_height == 1 else "Gen10-HD",
                    serial_number=f"SN{rack.name}{i + 1:03d}",
                    bmc_driver_type="simulated",
                    power_state=random.choice(["on", "on", "on", "off"]),
                )
                db.add(system)
                await db.flush()

                db.add(
                    PowerConnection(
                        system_id=system.id, pdu_outlet_id=outlets_a[i].id, psu_label="PSU1"
                    )
                )
                db.add(
                    PowerConnection(
                        system_id=system.id, pdu_outlet_id=outlets_b[i].id, psu_label="PSU2"
                    )
                )

                next_u += u_height + 1

        await db.commit()
        print(f"Seeded data center {dc.name!r} with {len(RACK_LAYOUT)} racks.")


if __name__ == "__main__":
    asyncio.run(seed())
