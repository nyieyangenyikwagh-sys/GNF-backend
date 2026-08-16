from fastapi import FastAPI
from app.api.v1 import auth,patients,insurance,claims,payments,appeals,analytics
from app.models import Base
from app.core.database import engine
Base.metadata.create_all(bind=engine)
app=FastAPI(title='Canadian Health Claims Platform',version='1.0.0')
for router in (auth.router,patients.router,insurance.router,claims.router,appeals.router,payments.router,analytics.router):app.include_router(router,prefix='/api/v1')
@app.get('/health')
def health():return {'status':'ok'}
