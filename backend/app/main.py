from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import csv
import io
import hashlib
from datetime import datetime

from .database import SessionLocal, engine, Base, get_db
from . import models, crud, schemas

# Create DB tables (if using SQLAlchemy metadata create)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daily Cash Transaction Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config: Known numbers (from fazle-core audit)
OWNER_PHONE = os.getenv("OWNER_PHONE", "8801880446111")
ACCOUNTANT_PHONE = os.getenv("ACCOUNTANT_PHONE", "8801844836824")


def is_cash_payment_intent(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    # crude heuristics: amount like 1000/- or mention bkash/nagad/cash or 'paid'
    if any(k in t for k in ["bkash", "nagad", "rocket", "cash"]) and ("/" in t or any(ch.isdigit() for ch in t)):
        return True
    # explicit amount pattern like 1000/-
    if "-/" in t or "/-" in t or "tk" in t or "taka" in t:
        return True
    if "paid" in t and any(ch.isdigit() for ch in t):
        return True
    return False


@app.get("/api/transactions", response_model=List[schemas.TransactionOut])
def list_transactions(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    txs = crud.get_transactions(db, skip=skip, limit=limit)
    return txs


@app.post("/api/transactions", response_model=schemas.TransactionOut)
def create_transaction(tx: schemas.TransactionCreate, db=Depends(get_db)):
    # If source is whatsapp, enforce employee_phone presence per requirement
    if tx.source == "whatsapp" and not tx.employee_phone:
        raise HTTPException(status_code=400, detail="employee_phone required for whatsapp source")
    db_tx = crud.create_transaction(db, tx)
    return db_tx


@app.post("/api/transactions/{tx_id}/approve", response_model=schemas.TransactionOut)
def approve_transaction(tx_id: int, approved_by: str, db=Depends(get_db)):
    tx = crud.get_transaction(db, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="transaction not found")
    tx = crud.approve_transaction(db, tx_id, approved_by)
    return tx


@app.post("/api/import_csv")
def import_csv(file: UploadFile = File(...), uploaded_by: Optional[str] = "web", db=Depends(get_db)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))
    errors = []
    success = 0
    total = 0
    for i, row in enumerate(reader, start=1):
        total += 1
        try:
            # map CSV columns to schema
            tx_data = schemas.TransactionCreate(
                source=row.get("source") or "import",
                source_message_ref=row.get("source_message_ref"),
                source_bridge=row.get("source_bridge"),
                employee_phone=row.get("employee_phone"),
                employee_name=row.get("employee_name"),
                payment_method=row.get("payment_method"),
                amount=float(row.get("amount") or 0),
                currency=row.get("currency") or "BDT",
                reference_number=row.get("reference_number"),
                transaction_date=row.get("transaction_date") or None,
                notes=row.get("notes"),
            )
            # name-only messages (no phone) are ignored per requirement
            if tx_data.source == "whatsapp" and not tx_data.employee_phone:
                continue
            crud.create_transaction(db, tx_data)
            success += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e), "row_data": row})
    job = crud.create_import_job(db, file.filename, uploaded_by, total, success, len(errors), errors)
    return {"job_id": job.id, "total": total, "success": success, "failures": len(errors)}


@app.post("/api/reconcile/messages")
def reconcile_messages(messages: List[dict], db=Depends(get_db)):
    """
    Accepts a list of message dicts with keys: message_id, sender, recipient, text, bridge
    Applies rule: process only if message has employee_phone or text contains phone, AND
    owner sent it AND recipient is accountant OR text addressed to accountant (simple heuristic).
    """
    created = 0
    skipped = 0
    for m in messages:
        sender = (m.get("sender") or "").replace("+", "")
        recipient = (m.get("recipient") or "").replace("+", "")
        text = m.get("text") or ""
        message_id = m.get("message_id")
        bridge = m.get("bridge")
        # check owner
        if sender != OWNER_PHONE:
            skipped += 1
            continue
        # check intended recipient accountant
        if recipient != ACCOUNTANT_PHONE and ACCOUNTANT_PHONE not in text:
            skipped += 1
            continue
        # try extract phone from text (simple 11-13 digit)
        import re
        phone_match = re.search(r"(?:\+?88)?0?1[3-9]\d{8}", text)
        employee_phone = phone_match.group(0) if phone_match else None
        if not employee_phone:
            # skip name-only per rule
            skipped += 1
            continue
        # only cash payment intents
        if not is_cash_payment_intent(text):
            skipped += 1
            continue
        # Create transaction draft
        tx_in = schemas.TransactionCreate(
            source="whatsapp",
            source_message_ref=message_id,
            source_bridge=bridge,
            employee_phone=employee_phone,
            employee_name=None,
            payment_method="cash",
            amount=float(re.sub(r"[^0-9.]", "", re.search(r"(\d+[.,]?\d*)", text).group(1))) if re.search(r"(\d+[.,]?\d*)", text) else 0,
            currency="BDT",
            reference_number=None,
            transaction_date=None,
            notes=text,
        )
        try:
            crud.create_transaction(db, tx_in)
            created += 1
        except Exception:
            skipped += 1
    return {"created": created, "skipped": skipped}
