"""python -m app.scripts.seed_settings"""
import asyncio

from app.db.init_db import seed_roles, seed_settings
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        await seed_roles(db)
        await seed_settings(db)
    print("Seeded roles and settings.")


if __name__ == "__main__":
    asyncio.run(main())
