from sqlalchemy import Column, Integer, Boolean, String, select, BigInteger, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# DATABASE_URL = "postgresql+asyncpg://school_api_3_user:lIlmLBoVtBcD6yqJ3AAIFVPsFgi5GkQy@dpg-cuaqparqf0us73cat8fg-a.oregon-postgres.render.com/school_api_3"
# DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_RkIy9Ctf5bph@ep-fragrant-butterfly-a8t65nyw-pooler.eastus2.azure.neon.tech/neondb"
# DATABASE_URL = "sqlite+aiosqlite:///database.sqlite3"
DATABASE_URL = "postgresql+asyncpg://postgres.wutuakdgbhffcpxcjsin:Mymodlyu0@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)


class BaseModel(AsyncAttrs, DeclarativeBase):
    pass


class School(BaseModel):
    __tablename__ = 'Logins_school'
    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True, nullable=False)  # ✅ Ensure uniqueness
    password = Column(String)
    password2 = Column(String)
    status = Column(Boolean, default=False)
    limit = Column(BigInteger)


class User(BaseModel):
    __tablename__ = 'Logins_user'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, nullable=False)  # ✅ Change to BigInteger
    name = Column(String)
    role = Column(String, default='User')
    sending = Column(Boolean, default=True)
    school_number = Column(String, ForeignKey('Logins_school.number'), nullable=True)

class Login(BaseModel):
    __tablename__ = 'Logins_logins_model'
    id = Column(Integer, primary_key=True)
    login = Column(String)
    password = Column(String)
    status = Column(Boolean, default=True)
    school_number = Column(String, ForeignKey('Logins_school.number', ondelete='CASCADE'),default=0)  # ✅ Corrected reference
    type = Column(String)


async def get_users():
    async with async_session() as session:
        user = await session.execute(select(User).where(User.sending == True))
        users = user.scalars().all()
        return users


async def get_user(tg_id):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        users = user.scalar_one_or_none()
        return users


async def get_admin(tg_id):
    async with async_session() as session:
        admin = await session.execute(select(User).where(User.tg_id == tg_id))
        admins = admin.scalar()
        if admins.role == 'Superuser':
            return True
        return False


async def get_users_all():
    async with async_session() as session:
        user = await session.execute(select(User.tg_id))
        users = user.scalars().all()
        return users


async def create_user(tg_id,name, sending=None, role='User'):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalars().first()

        if user:
            if sending != 'org':
                user.sending = sending

        else:
            user = User(tg_id=tg_id, sending=sending, name=name, school_number=None, role=role)
            session.add(user)

        await session.commit()
        await session.refresh(user)  # ✅ Keep user attached to session
        return user  # Still attached

async def make_admin(tg_id, role='Superuser'):
    async with (async_session() as session):
        t = await session.execute(select(User).where(User.tg_id == tg_id))
        r = t.scalar_one_or_none()
        if r:
            r.sending = True
            r.role = role
            await session.commit()
            return True  # ✅ Return success flag
        else:
            user = User(tg_id=tg_id,sending=True, role=role,school_number=0)
            session.add(user)
            await session.commit()
            return True



async def change_user_status(tg_id, status=False):
    async with async_session() as session:
        user = await session.execute(select(User).where(User.tg_id == tg_id))
        user = user.scalar_one_or_none()
        if user:
            user.school_number = status
        await session.commit()


async def change_school_number(tg_id, school_number):
    async with async_session() as session:
        t = await session.execute(select(User).where(User.tg_id == tg_id))
        r = t.scalar_one_or_none()
        if r:
            j = await session.execute(select(School).where(School.number == school_number))
            l = j.scalar_one_or_none()
            if not l:
                new_school = School(number=school_number,password='<$*$*$=$/>',password2='xusanboyman')
                session.add(new_school)
                await session.commit()
                await session.flush()
            r.school_number = school_number
        await session.commit()
        return


async def get_login_all():
    async with async_session() as session:
        result = await session.execute(select(Login))
        logins = result.scalars().all()
        return logins


async def get_login(school_number):
    async with async_session() as session:
        result = await session.execute(select(Login).where(Login.school_number == school_number))
        logins = result.scalars().all()
        return logins


async def get_login1():
    async with async_session() as session:
        result = await session.execute(select(Login).order_by(Login.type))
        logins = result.scalars().all()
        return logins


async def delete_login(login):
    async with async_session() as session:
        async with session.begin():
            data = await session.execute(select(Login).where(Login.login == login))
            l = data.scalar_one_or_none()
            print(l.login,l.id)
            if l:
                await session.delete(l)
                return True
            return False


async def create_login(login: str, password: str, status: bool, school_number: int, type: str):
    async with async_session() as session:
        async with session.begin():
            existing_login = await session.execute(select(Login).where(Login.login == login))
            existing_login = existing_login.scalar_one_or_none()
            if existing_login:
                existing_login.password = password
                existing_login.status = status
                session.add(existing_login)
                await session.commit()
                return existing_login
            else:
                new_login = Login(login=login, password=password, status=status, school_number=school_number, type=type)
                session.add(new_login)
                await session.commit()
                return new_login

async def init():
    async with engine.begin() as conn:
        # await conn.run_sync(BaseModel.metadata.drop_all)  # Drop all tables first
        await conn.run_sync(BaseModel.metadata.create_all)  # Recreate tables with fixes

# async def init():
#     async with engine.begin() as conn:
#         await conn.run_sync(BaseModel.metadata.create_all)
