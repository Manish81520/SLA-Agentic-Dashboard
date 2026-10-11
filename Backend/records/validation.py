"""Validation for partner-add and partner-edit payloads."""
import math
from Backend.calculations.normalization import _is_missing, coerce_duration, parse_iso_date
from Agents.ExcelAnalyst.data_cleaner import is_supported_iso_date
M_REQUIRED="This field is required."; M_DATE="Enter a valid date (YYYY-MM-DD)."; M_NUMBER="Enter a valid number."; M_RANGE="Enter a number from 0 to 365."; M_ORDER="Must not be before “{start}”."; M_GAP="The gap between these dates must be 365 days or less."; M_DUP="A partner with this identifier already exists."; M_LOCKED="The identifier cannot be changed."; M_UNKNOWN="Unknown field."; M_AUTO="This field is calculated automatically."; M_SUMMARY="Please fix the highlighted fields."
def prepare_row(schema,incoming,existing):
    base={c:None for c in schema.columns} if existing is None else dict(existing); errors={}; clean={}
    for key,value in incoming.items():
        field=schema.field(key)
        if not field: errors[key]=M_UNKNOWN; continue
        if field.auto: errors[key]=M_AUTO; continue
        if existing is not None and field.role=="identifier":
            if (str(value).strip().casefold() if not _is_missing(value) else None)==(str(base.get(key)).strip().casefold() if not _is_missing(base.get(key)) else None): continue
            errors[key]=M_LOCKED; continue
        if field.type=="text": clean[key]=None if value is None or str(value).strip()=="" else str(value).strip()
        elif field.type=="date":
            if _is_missing(value): clean[key]=None
            elif is_supported_iso_date(str(value)): clean[key]=str(value).strip().replace("/","-")
            else: errors[key]=M_DATE
        else:
            if _is_missing(value): clean[key]=None
            else:
                try: n=float(str(value).strip()); assert math.isfinite(n)
                except (ValueError,AssertionError): errors[key]=M_NUMBER; continue
                if field.role=="stageDuration" and not 0<=n<=365: errors[key]=M_RANGE
                else: clean[key]=int(n) if n.is_integer() else n
    base.update(clean)
    for field in schema.fields:
        if field.required and (existing is None or field.key in incoming) and _is_missing(base.get(field.key)): errors[field.key]=M_REQUIRED
    for a,b,error_key in schema.order_rules:
        if existing is None or a in incoming or b in incoming:
            av,_=parse_iso_date(base.get(a)); bv,_=parse_iso_date(base.get(b))
            if av and bv and bv<av: errors[error_key]=M_ORDER.format(start=a)
    for a,b,d in schema.sync_rules:
        if existing is None or a in incoming or b in incoming:
            av,_=parse_iso_date(base.get(a)); bv,_=parse_iso_date(base.get(b))
            if av and bv and b not in errors:
                days=(bv-av).days; val,reason=coerce_duration(days)
                if reason: errors[b]=M_GAP
                else: base[d]=int(val)
    value=base.get(schema.identifier_key) if schema.identifier_key else None
    return base,(None if _is_missing(value) else str(value).strip().casefold()),errors
