from datetime import date
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.insurance import InsurancePlan,PatientInsurance
from app.models.patient import Patient
from app.models.provincial_rule import ProvincialRule
from app.services.eligibility import verify_eligibility
def run():
 db=SessionLocal()
 if not db.query(User).filter(User.email=='admin@demo.ca').first():db.add(User(email='admin@demo.ca',hashed_password=hash_password('admin123'),role='admin'))
 for p in [InsurancePlan(payer_id='AHCIP',name='Alberta Health Care Insurance Plan (AHCIP)',layer='public',plan_type='public'),InsurancePlan(payer_id='GREENSHIELD',name='Green Shield Canada',layer='private',plan_type='EHB')]:
  if not db.query(InsurancePlan).filter(InsurancePlan.payer_id==p.payer_id).first():db.add(p)
 db.commit()
 if not db.query(Patient).first():
  p=Patient(first_name='Jordan',last_name='Lee',dob=date(1990,5,1),gender='other',province='AB');db.add(p);db.flush();plan=db.query(InsurancePlan).filter(InsurancePlan.payer_id=='AHCIP').first();db.add(PatientInsurance(patient_id=p.id,plan_id=plan.id,member_id='MEM-1001',health_card_number='123456789',effective_date=date(2024,1,1),priority='primary'));db.commit()
 db.close();print('Seed complete. Login: admin@demo.ca / admin123')
if __name__=='__main__':run()
