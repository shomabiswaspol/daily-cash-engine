from sqlalchemy import Column, Integer, Text, Numeric, Date, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class DailyCashTransaction(Base):
    __tablename__ = "daily_cash_transactions"
    id = Column(Integer, primary_key=True, index=True)
    txn_ref = Column(Text, unique=True, nullable=True)
    source = Column(Text)
    source_message_ref = Column(Text)
    source_bridge = Column(Text)
    employee_id = Column(Integer, nullable=True)
    employee_name = Column(Text, nullable=True)
    employee_phone = Column(Text, nullable=True)
    payment_method = Column(Text, nullable=True)
    amount = Column(Numeric(12,2), nullable=False)
    currency = Column(Text, default='BDT')
    reference_number = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=True)
    transaction_time = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Text, nullable=True)
    approved_by = Column(Text, nullable=True)
    approval_status = Column(Text, default='pending')
    transaction_status = Column(Text, default='pending')
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DailyImportJob(Base):
    __tablename__ = "daily_import_jobs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(Text)
    uploaded_by = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    row_count = Column(Integer, nullable=True)
    success_count = Column(Integer, nullable=True)
    failure_count = Column(Integer, nullable=True)
    errors = Column(JSON, nullable=True)
    importer_settings = Column(JSON, nullable=True)

class DailyAuditLog(Base):
    __tablename__ = "daily_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    txn_id = Column(Integer, nullable=True)
    action = Column(Text)
    actor = Column(Text)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
