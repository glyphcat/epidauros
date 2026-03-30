from sqlalchemy import Column, String, Integer, Numeric, Text, ARRAY, DateTime, Date, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.core.database import Base

class Actor(Base):
    __tablename__ = "actors"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(Text, nullable=False)
    external_id = Column(Text, unique=True)
    gender = Column(Integer)  # TMDB spec: 0=Not set/spec, 1=Female, 2=Male, 3=Non-binary
    birth_date = Column(Date)
    current_guarantee_score = Column(Numeric(6, 5))
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    performances = relationship("Performance", back_populates="actor", cascade="all, delete-orphan")

class Work(Base):
    __tablename__ = "works"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(Text, nullable=False)
    external_id = Column(Text, unique=True)
    release_year = Column(Integer)
    plot_full = Column(Text, nullable=False)
    director = Column(Text)
    genre = Column(Text)
    box_office = Column(Numeric)
    setting_period = Column(Text)
    setting_location = Column(Text)
    plot_embedding_id = Column(UUID(as_uuid=True))
    scenario_graph_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    performances = relationship("Performance", back_populates="work", cascade="all, delete-orphan")

class Performance(Base):
    __tablename__ = "performances"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    work_id = Column(UUID(as_uuid=True), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="CASCADE"), nullable=False)
    character_name = Column(Text, nullable=False)
    expected_guarantee_rank = Column(Text)
    success_score = Column(Numeric(6, 5))
    character_vector_id = Column(UUID(as_uuid=True))
    source_situation_ids = Column(ARRAY(Text))
    target_situation_ids = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    __table_args__ = (UniqueConstraint('work_id', 'actor_id', 'character_name', name='uq_perf_work_actor_char'),)

    work = relationship("Work", back_populates="performances")
    actor = relationship("Actor", back_populates="performances")
