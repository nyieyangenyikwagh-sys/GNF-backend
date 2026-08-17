export type Role = "admin" | "analyst" | "biller" | string;
export interface User { id: number; email: string; role: Role; is_active?: boolean; created_at?: string }
export interface InsurancePlan { id?: number; payer_id: string; member_id: string; health_card_number?: string | null; group_number?: string | null; effective_date: string; termination_date?: string | null; priority: string }
export interface Patient { id: number; first_name: string; last_name: string; dob?: string; gender?: string; province: string; phone?: string; email?: string; created_at?: string; insurance?: InsurancePlan }
export interface ClaimLine { id?: number; service_code: string; diagnosis_code: string; units: number; amount: number }
export interface RuleViolation { code: string; message: string; severity?: "error" | "warning" }
export interface Claim { id: number; patient_id?: number; plan_id?: number; status: string; province: string; provider_billing_number?: string; service_date?: string; billed_amount: number; denial_reason_code?: string | null; lines: ClaimLine[]; rule_violations?: RuleViolation[]; created_at?: string; updated_at?: string }
export interface Appeal { id: number; claim_id: number; outcome: string; note?: string; supporting_doc_url?: string; created_at?: string }
export interface Payment { id: number; claim_id: number; era_number?: string; paid_amount: number; underpaid: boolean; posted_at?: string }
export interface AnalyticsSummary { denial_rate_by_payer: { payer_id: string; total: number; denied: number; denial_rate: number }[]; top_denial_reasons: Record<string, number>; appeal_success_rate: number; avg_days_to_payment: number | null }
export interface Eligibility { eligible: boolean; reason?: string | null; member_id: string; payer_id: string; plan_name: string; plan_type: string; coinsurance: number; verified_at: string }
