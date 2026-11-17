from sqlalchemy import String, Float, Integer, ForeignKey, JSON, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from src.config.database import Base
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password_hash:Mapped[str]=mapped_column(String(300))
    role:Mapped[str]=mapped_column(String(20))
class Batch(Base):
    __tablename__="batches"
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(50),unique=True)
    line:Mapped[str]=mapped_column(String(20))
    supplier:Mapped[str]=mapped_column(String(80))
    tonnes:Mapped[float]=mapped_column(Float)
    received_date:Mapped[str]=mapped_column(String(10))
class Inspection(Base):
    __tablename__="inspections"
    id:Mapped[int]=mapped_column(primary_key=True)
    sample_code:Mapped[str]=mapped_column(String(70),unique=True)
    batch_id:Mapped[int]=mapped_column(ForeignKey("batches.id"))
    flour_yield:Mapped[float]=mapped_column(Float)
    moisture:Mapped[float]=mapped_column(Float)
    inspector:Mapped[str]=mapped_column(String(50))
class Review(Base):
    __tablename__="reviews"
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(120))
    line:Mapped[str]=mapped_column(String(20))
    status:Mapped[str]=mapped_column(String(20),default="queued")
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    snapshot:Mapped[list]=mapped_column(JSON,default=list)
    note:Mapped[str]=mapped_column(Text,default="")
    created_by:Mapped[str]=mapped_column(String(100))
    approved_by:Mapped[str]=mapped_column(String(100),default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Audit(Base):
    __tablename__="audits"
    id:Mapped[int]=mapped_column(primary_key=True)
    actor:Mapped[str]=mapped_column(String(100))
    action:Mapped[str]=mapped_column(String(200))
    status:Mapped[int]=mapped_column(Integer)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class BlindOrder(Base):
    __tablename__="blind_orders"
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(120))
    status:Mapped[str]=mapped_column(String(20),default="sealed")
    tolerance:Mapped[float]=mapped_column(Float)
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    created_by:Mapped[str]=mapped_column(String(100))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    unblinded_by:Mapped[str]=mapped_column(String(100),default="")
    unblinded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=True)
class BlindItem(Base):
    __tablename__="blind_items"
    __table_args__=(UniqueConstraint('order_id','anon_code'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    order_id:Mapped[int]=mapped_column(ForeignKey("blind_orders.id"))
    anon_code:Mapped[str]=mapped_column(String(20))
    inspection_id:Mapped[int]=mapped_column(ForeignKey("inspections.id"))
    sample_code:Mapped[str]=mapped_column(String(70))
    batch_code:Mapped[str]=mapped_column(String(50))
    original_yield:Mapped[float]=mapped_column(Float)
    external_email:Mapped[str]=mapped_column(String(100))
    retest_yield:Mapped[float]=mapped_column(Float,nullable=True)
    status:Mapped[str]=mapped_column(String(20),default="pending")
class BlindBackfill(Base):
    __tablename__="blind_backfills"
    id:Mapped[int]=mapped_column(primary_key=True)
    item_id:Mapped[int]=mapped_column(ForeignKey("blind_items.id"))
    value:Mapped[float]=mapped_column(Float)
    kind:Mapped[str]=mapped_column(String(20))
    submitted_by:Mapped[str]=mapped_column(String(100))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
