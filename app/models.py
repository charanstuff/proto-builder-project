# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table between Campaigns and Leads
campaign_leads = Table(
    'campaign_leads',
    Base.metadata,
    Column('campaign_id', Integer, ForeignKey('campaigns.id'), primary_key=True),
    Column('lead_id', Integer, ForeignKey('leads.id'), primary_key=True),
    Column('last_contact_date', DateTime, nullable=True),
    Column('next_followup_date', DateTime, nullable=True),
    Column('message_history', Text, nullable=True)
)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    subject = Column(String(255))
    follow_up_interval = Column(Integer, default=3)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    leads = relationship("Lead", secondary=campaign_leads, back_populates="campaigns")
    messages = relationship("Message", backref="campaign")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    status = Column(String(50), default="new")
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", secondary=campaign_leads, back_populates="leads")
    messages = relationship("Message", backref="lead")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    direction = Column(String(20))  # 'inbound' or 'outbound'
    content = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)

# New Model: LLMConfig for LLM Manager
class LLMConfig(Base):
    __tablename__ = "llm_config"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(50))
    api_key = Column(String(255))
    settings = Column(Text)  # Store additional settings as JSON string

# New Model: OutreachLog for Outreach Engine & Follow-Up
class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="sent")

# New Model: ClassificationLog for Scoring & Classification
class ClassificationLog(Base):
    __tablename__ = "classification_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    classification_result = Column(String(50))
    score = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

# New Model: ProductContext for Product Context & Use-Case Definition
class ProductContext(Base):
    __tablename__ = "product_context"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Simplified user identifier
    context_data = Column(Text)  # JSON string representing product context
    updated_at = Column(DateTime, default=datetime.utcnow)
