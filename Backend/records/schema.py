"""Derive an editable record schema from persisted source data."""
from dataclasses import dataclass
from typing import Any
import pandas as pd
from Agents.ExcelAnalyst.data_cleaner import is_supported_iso_date
from Backend.calculations.configuration import configuration_from_agent
from Backend.calculations.normalization import _is_missing, parse_iso_date
from Backend.db.repository import LoadedDataset

@dataclass(frozen=True)
class FieldDef:
    key: str; label: str; role: str; type: str; required: bool; locked: bool; auto: bool; not_before: str | None; options: list[str]; min: int | None; max: int | None; section: str | None
@dataclass
class RecordSchema:
    dataset_id: int; revision: int; filename: str; columns: list[str]; fields: list[FieldDef]; sections: list[dict]; warnings: list[str]; identifier_key: str | None; partner_name_key: str | None; has_completion: bool; order_rules: list[tuple[str,str,str]]; sync_rules: list[tuple[str,str,str]]
    def field(self, key): return next((field for field in self.fields if field.key == key), None)
    def to_api(self):
        return {"datasetId":self.dataset_id,"revision":self.revision,"filename":self.filename,"identifierKey":self.identifier_key,"partnerNameKey":self.partner_name_key,"hasCompletion":self.has_completion,"warnings":self.warnings,"sections":[{"id":s["id"],"title":s["title"],"collapsed":s["collapsed"],"fieldKeys":s["fieldKeys"]} for s in self.sections],"fields":[{"key":f.key,"label":f.label,"role":f.role,"type":f.type,"required":f.required,"locked":f.locked,"auto":f.auto,"notBefore":f.not_before,"options":f.options,"min":f.min,"max":f.max} for f in self.fields]}

def build_schema(loaded: LoadedDataset) -> RecordSchema:
    config=configuration_from_agent(loaded.agent_response); cols=loaded.columns; warnings=[]
    mapped=[config.identifier_column,config.partner_name_column,config.group_column,config.onboarding_start_column,config.completion_column]+[x for st in config.stages for x in (st.start_column,st.end_column,st.duration_column)]
    for key in mapped:
        if key and key not in cols: warnings.append(f"Mapped column “{key}” was not found in the data.")
    def available(key): return key if key in cols else None
    ident,name,team,start,completion=map(available,(config.identifier_column,config.partner_name_column,config.group_column,config.onboarding_start_column,config.completion_column))
    if not ident: warnings.insert(0,"No identifier column was detected, so duplicate partners can’t be prevented.")
    if not name: warnings.append("No partner name column was detected; the table shows generated names.")
    if not completion: warnings.append("No completion date column was detected, so every partner shows as In progress.")
    roles={}; stage_by={}; autos=set(); order=[]; sync=[]
    for key,role in ((ident,"identifier"),(name,"partnerName"),(team,"team"),(start,"onboardingStart"),(completion,"completion")):
        if key: roles.setdefault(key,role)
    for i,st in enumerate(config.stages):
        a,b,d=map(available,(st.start_column,st.end_column,st.duration_column))
        for key,role in ((a,"stageStart"),(b,"stageEnd"),(d,"stageDuration")):
            if key: roles.setdefault(key,role); stage_by.setdefault(key,i)
        if a and b: order.append((a,b,b))
        if a and b and d:
            valid=[]
            for _,row in loaded.dataframe.iterrows():
                sd,_=parse_iso_date(row[a]); ed,_=parse_iso_date(row[b]); value=row[d]
                if sd and ed and not _is_missing(value):
                    try: valid.append(float(value)==(ed-sd).days)
                    except (TypeError,ValueError): valid.append(False)
            if valid and all(valid): autos.add(d); sync.append((a,b,d))
    if start and completion: order.append((start,completion,completion))
    def kind(key,role):
        series=loaded.dataframe[key]; non=[v for v in series if not _is_missing(v)]
        if role in {"onboardingStart","completion","stageStart","stageEnd"}: return "date"
        if role=="stageDuration" or (pd.api.types.is_numeric_dtype(series) and non): return "number"
        return "date" if role=="other" and non and all(is_supported_iso_date(str(v)) for v in non) else "text"
    fields=[]
    for key in cols:
        role=roles.get(key,"other"); typ=kind(key,role); values=[str(v) for v in loaded.dataframe[key] if not _is_missing(v)]; distinct=sorted(set(values)); opts=distinct if role not in {"identifier","partnerName"} and typ=="text" and 2<=len(distinct)<=50 and len(distinct)<len(values) else []
        nb=start if role=="completion" else None
        if role=="stageEnd":
            st=config.stages[stage_by[key]]; candidate=available(st.start_column); nb=candidate
        auto=key in autos
        fields.append(FieldDef(key,key,role,typ,role in {"identifier","partnerName"},role=="identifier",auto,nb,opts,0 if role=="stageDuration" and not auto else None,365 if role=="stageDuration" and not auto else None,None))
    groups=[("overview","Overview",False,[x for x in (ident,name,team,start,completion) if x])]
    placed=set(groups[0][3])
    for i,st in enumerate(config.stages):
        keys=[x for x in (available(st.start_column),available(st.end_column),available(st.duration_column)) if x and x not in placed]
        if keys: groups.append((f"stage-{i}",st.label,False,keys)); placed.update(keys)
    other=[c for c in cols if c not in placed]
    if other: groups.append(("other","Other fields",True,other))
    sections=[{"id":a,"title":b,"collapsed":c,"fieldKeys":d} for a,b,c,d in groups if d]
    section_map={key:s["id"] for s in sections for key in s["fieldKeys"]}
    fields=[FieldDef(**{**f.__dict__,"section":section_map.get(f.key)}) for f in fields]
    return RecordSchema(loaded.dataset_id,loaded.revision,loaded.filename,cols,fields,sections,warnings,ident,name,bool(completion),list(dict.fromkeys(order)),sync)
