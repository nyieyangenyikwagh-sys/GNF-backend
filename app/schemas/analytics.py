from pydantic import BaseModel
class DenialByPayer(BaseModel): payer_id:str; total:int; denied:int; denial_rate:float
class AnalyticsSummary(BaseModel): denial_rate_by_payer:list[DenialByPayer]; top_denial_reasons:dict[str,int]; appeal_success_rate:float; avg_days_to_payment:float|None
