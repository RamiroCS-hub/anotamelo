"""Script para configurar un usuario como PREMIUM."""
import asyncio
import sys

from app.db.database import async_session_maker
from app.db.models import User
from sqlalchemy import select


async def set_premium(whatsapp_number: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.whatsapp_number == whatsapp_number)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ Usuario {whatsapp_number} no encontrado")
            return
        
        user.plan = "PREMIUM"
        await session.commit()
        print(f"✅ Usuario {whatsapp_number} actualizado a PREMIUM")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python set_premium.py <numero_whatsapp>")
        print("Ejemplo: python set_premium.py 5491123456789")
        sys.exit(1)
    
    asyncio.run(set_premium(sys.argv[1]))
