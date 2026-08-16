import re
from dataclasses import dataclass
from datetime import date,timedelta
from app.reference.ahs_codes import AHS_SERVICE_CODES
from app.reference.icd10ca import ICD10CA_CODES
PROVINCE_CONFIG={"AB":{"billing_number_re":r"^\d{6}$","filing_limit_days":90,"health_card_re":r"^\d{9}$"},"ON":{"billing_number_re":r"^\d{6}$","filing_limit_days":183,"health_card_re":r"^\d{10}[A-Z]{2}$"}}
@dataclass
class RuleError: code:str; message:str
@dataclass
class ClaimContext: province:str; provider_billing_number:str; service_date:date; health_card_number:str|None; patient_province:str; lines:list[dict]
def run_rules(c):
 e=[];cfg=PROVINCE_CONFIG.get(c.province,{})
 if not c.lines:e.append(RuleError("R001","Claim has no service lines"))
 if not c.provider_billing_number:e.append(RuleError("R001","Missing provider billing number"))
 if cfg and not re.match(cfg['billing_number_re'],c.provider_billing_number):e.append(RuleError("R002",f"Billing number invalid for {c.province}"))
 e += [RuleError("R003",f"Unknown ICD-10-CA code {x['diagnosis_code']}") for x in c.lines if x['diagnosis_code'] not in ICD10CA_CODES]
 e += [RuleError("R004",f"Unknown AHCIP SOMB code {x['service_code']}") for x in c.lines if x['service_code'] not in AHS_SERVICE_CODES]
 if c.service_date<date.today()-timedelta(days=cfg.get('filing_limit_days',90)):e.append(RuleError("R005","Past the timely-filing limit"))
 if cfg and (not c.health_card_number or not re.match(cfg['health_card_re'],c.health_card_number)):e.append(RuleError("R009",f"Invalid {c.province} health card"))
 if c.patient_province!=c.province:e.append(RuleError("R010",f"Patient ({c.patient_province}) cannot be billed to {c.province}"))
 return e
