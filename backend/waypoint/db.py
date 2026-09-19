from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, String, JSON, ForeignKey, event, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DB_URL, DATA

def now():
    return datetime.now(timezone.utc).isoformat()
def uid():
    return uuid4().hex

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String, default='')
    created_at: Mapped[str] = mapped_column(String, default=now)

class Record(Base):
    __tablename__ = 'records'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey('projects.id'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String, default=now)

class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey('projects.id'), index=True)
    kind: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default='queued', index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String, default='Waiting for worker')
    config: Mapped[dict] = mapped_column(JSON)
    result_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default=now)
    updated_at: Mapped[str] = mapped_column(String, default=now)

class Device(Base):
    __tablename__ = 'devices'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String)
    token_hash: Mapped[str] = mapped_column(String)
    revoked: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, default=now)

class Batch(Base):
    __tablename__ = 'batches'
    __table_args__ = (UniqueConstraint('device_id', 'session_id', 'sequence'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    device_id: Mapped[str] = mapped_column(ForeignKey('devices.id'))
    session_id: Mapped[str] = mapped_column(String)
    sequence: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String, default=now)

engine = create_engine(DB_URL, connect_args={'check_same_thread': False, 'timeout': 30})
@event.listens_for(engine, 'connect')
def pragmas(connection, _):
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('PRAGMA journal_mode=WAL')
Session = sessionmaker(engine, expire_on_commit=False)

# A separate SQLite connection enforces read-only queries at the database layer.
# SQLite has no database user roles; mutation endpoints retain the writer engine.
read_engine = create_engine(
    f"sqlite:///file:{(DATA / 'waypoint.db').as_posix()}?mode=ro&uri=true",
    connect_args={'check_same_thread': False, 'timeout': 30},
)
@event.listens_for(read_engine, 'connect')
def read_only(connection, _):
    connection.execute('PRAGMA query_only=ON')
ReadSession = sessionmaker(read_engine, expire_on_commit=False)

def migrate():
    # Versioned, transactional migration; deliberately independent of web startup order.
    from sqlalchemy import text
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)'))
        version = connection.execute(text('SELECT MAX(version) FROM schema_version')).scalar() or 0
        if version > 1:
            raise RuntimeError('Workspace was created by a newer version')
        if version < 1:
            Base.metadata.create_all(connection)
            connection.execute(text('INSERT INTO schema_version VALUES (1)'))

def record_dict(record):
    return {c.name: getattr(record, c.name) for c in record.__table__.columns if c.name != 'token_hash'}
