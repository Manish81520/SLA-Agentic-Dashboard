"""Transactional partner record operations."""
from sqlalchemy.exc import IntegrityError
from Backend.calculations import calculate_partners_list
from Backend.db import repository as repo
from Backend.db.session import session_scope
from .schema import build_schema
from .validation import M_DUP, prepare_row
NoActiveDataset=repo.NoActiveDataset
class RecordValidationError(Exception):
    def __init__(self,field_errors): self.field_errors=field_errors
class RecordNotFound(Exception): pass
def get_schema_payload():
    with session_scope() as s: return build_schema(repo.load_active(s)).to_api()
def get_rows_payload():
    with session_scope() as s:
        loaded=repo.load_active(s); derived={p["rowId"]:p for p in calculate_partners_list(loaded.dataframe,loaded.agent_response)["partners"]}
        return {"datasetId":loaded.dataset_id,"revision":loaded.revision,"rows":[{"rowId":row_id,"fields":{c:data.get(c) for c in loaded.columns},"derived":{k:derived[row_id][k] for k in ("partnerName","team","currentStage","status","onboardingDays")}} for row_id,data in loaded.rows.items()]}
def _write(row_id,fields):
    with repo.WRITE_LOCK:
        with session_scope() as s:
            loaded=repo.load_active(s); schema=build_schema(loaded); row=None
            if row_id is not None:
                row=repo.get_row(s,loaded.dataset_id,row_id)
                if not row: raise RecordNotFound()
            data,norm,errors=prepare_row(schema,fields,None if row is None else row.data)
            if row is None and not errors and norm is not None and repo.identifier_exists(s,loaded.dataset_id,norm): errors[schema.identifier_key]=M_DUP
            if errors: raise RecordValidationError(errors)
            try:
                target=repo.insert_row(s,loaded.dataset_id,data,norm) if row is None else row
                if row is not None: repo.update_row(s,row,data)
                revision=repo.bump_revision(s,loaded.dataset_id)
            except IntegrityError as exc: raise RecordValidationError({schema.identifier_key:M_DUP}) from exc
            return {"rowId":target.id,"revision":revision}
def add_partner(fields): return _write(None,fields)
def update_partner(row_id,fields): return _write(row_id,fields)
