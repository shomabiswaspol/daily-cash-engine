from pydantic import BaseModel
from typing import Optional
from datetime import date

class TransactionBase(BaseModel):
    source: Optional[str] = "web"
    source_message_ref: Optional[str]
    source_bridge: Optional[str]
    employee_phone: Optional[str]
    employee_name: Optional[str]
    payment_method: Optional[str] = "cash"
    amount: float
    currency: Optional[str] = "BDT"
    reference_number: Optional[str]
    transaction_date: Optional[str]
    notes: Optional[str]

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int
    approval_status: str
    transaction_status: str
    is_reconciled: bool
    created_at: str

    class Config:
        orm_mode = True
