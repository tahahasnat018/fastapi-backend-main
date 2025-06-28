from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import SMEmployeeRoleType
from schemas import SMEmployeeRoleTypeCreate, SMEmployeeRoleTypeUpdate
from sqlalchemy import select
from fastapi import HTTPException, status

async def create_role_type(db: AsyncSession, data: SMEmployeeRoleTypeCreate):
    # Check if a role with the same code already exists
    existing = await db.execute(
        select(SMEmployeeRoleType).where(SMEmployeeRoleType.code == data.code)
    )
    role_in_db = existing.scalar_one_or_none()

    if role_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with code '{data.code}' already exists."
        )

    # Create and insert new role
    new_role = SMEmployeeRoleType(**data.dict())
    db.add(new_role)
    await db.commit()
    await db.refresh(new_role)
    return new_role


async def get_all_roles(db: AsyncSession, business_owner_id: int):
    result = await db.execute(
        select(SMEmployeeRoleType).where(SMEmployeeRoleType.business_owner_id == business_owner_id)
    )
    return result.scalars().all()

async def get_role(db: AsyncSession, role_id: int):
    result = await db.execute(select(SMEmployeeRoleType).where(SMEmployeeRoleType.id == role_id))
    return result.scalar_one_or_none()


from datetime import datetime

async def update_role(db: AsyncSession, role_id: int, data: SMEmployeeRoleTypeUpdate):
    role = await get_role(db, role_id)
    if not role:
        return None
    for key, value in data.dict().items():
        setattr(role, key, value)
    role.updated_at = datetime.utcnow()  # <- force update
    await db.commit()
    await db.refresh(role)
    return role

async def delete_role(db: AsyncSession, role_id: int):
    role = await get_role(db, role_id)
    if not role:
        return None
    await db.delete(role)
    await db.commit()
    return role
