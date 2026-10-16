from sqlalchemy.orm import Session
from . import models, schemas
import hashlib
from datetime import datetime


def _make_txn_ref(data: schemas.TransactionCreate) -> str:
    raw = f"{data.source}|{data.source_message_ref or ''}|{data.employee_phone or ''}|{data.amount}|{data.reference_number or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DailyCashTransaction).order_by(models.DailyCashTransaction.created_at.desc()).offset(skip).limit(limit).all()


def get_transaction(db: Session, tx_id: int):
    return db.query(models.DailyCashTransaction).filter(models.DailyCashTransaction.id == tx_id).first()


def create_transaction(db: Session, tx: schemas.TransactionCreate):
    txn_ref = _make_txn_ref(tx)
    # idempotency: if txn_ref exists, return existing
    existing = db.query(models.DailyCashTransaction).filter(models.DailyCashTransaction.txn_ref == txn_ref).first()
    if existing:
        return existing
    db_tx = models.DailyCashTransaction(
        txn_ref=txn_ref,
        source=tx.source,
        source_message_ref=tx.source_message_ref,
        source_bridge=tx.source_bridge,
        employee_phone=tx.employee_phone,
        employee_name=tx.employee_name,
        payment_method=tx.payment_method,
        amount=tx.amount,
        currency=tx.currency,
        reference_number=tx.reference_number,
        transaction_date=datetime.strptime(tx.transaction_date, "%Y-%m-%d").date() if tx.transaction_date else None,
        notes=tx.notes,
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    # audit log
    from .models import DailyAuditLog
    log = DailyAuditLog(txn_id=db_tx.id, action="created", actor=tx.source, payload={"txn_ref": db_tx.txn_ref})
    db.add(log)
    db.commit()
    return db_tx


def approve_transaction(db: Session, tx_id: int, approved_by: str):
    tx = get_transaction(db, tx_id)
    if not tx:
        return None
    tx.approval_status = "approved"
    tx.approved_by = approved_by
    tx.transaction_status = "final"
    db.add(tx)
    db.commit()
    db.refresh(tx)
    from .models import DailyAuditLog
    log = DailyAuditLog(txn_id=tx.id, action="approved", actor=approved_by, payload={})
    db.add(log)
    db.commit()
    return tx


def create_import_job(db: Session, filename: str, uploaded_by: str, row_count: int, success_count: int, failure_count: int, errors: list):
    job = models.DailyImportJob(filename=filename, uploaded_by=uploaded_by, row_count=row_count, success_count=success_count, failure_count=failure_count, errors=errors)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
