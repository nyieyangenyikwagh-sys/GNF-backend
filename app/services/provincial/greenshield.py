import json
from app.services.provincial.base import ProvincialBillingEngine
class GreenShieldEngine(ProvincialBillingEngine):
 province="GREENSHIELD"
 def format_submission(self,claim):return json.dumps({"provider":claim.provider_billing_number,"serviceDate":str(claim.service_date),"lines":[{"code":x.service_code,"dx":x.diagnosis_code,"amount":float(x.amount)} for x in claim.lines]}).encode()
 def verify_eligibility_format(self,health_card):return True
