import re
from app.services.provincial.base import ProvincialBillingEngine
class AHSEngine(ProvincialBillingEngine):
 province="AB"
 def format_submission(self,claim):return (f"AHCIP|{claim.provider_billing_number}|{claim.service_date}\n"+"\n".join(f"{x.service_code}|{x.diagnosis_code}|{x.units}|{x.amount}" for x in claim.lines)).encode()
 def verify_eligibility_format(self,health_card):return bool(re.match(r"^\d{9}$",health_card or ""))
