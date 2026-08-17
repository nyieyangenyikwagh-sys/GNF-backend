"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { Appeal } from "@/lib/types";
export default function AppealDetail({ params }: { params: Promise<{ id: string }> }) { const [appeal, setAppeal] = useState<Appeal | null>(null); useEffect(() => { params.then(({ id }) => api.get(`/appeals/${id}`).then(r => setAppeal(r.data)).catch(() => {})); }, [params]); return appeal ? <><h1 className="text-2xl font-bold">Appeal #{appeal.id}</h1><div className="mt-6 rounded-xl border bg-white p-5"><p><span className="text-slate-500">Claim:</span> #{appeal.claim_id}</p><p className="mt-2"><span className="text-slate-500">Outcome:</span> <span className="font-semibold capitalize">{appeal.outcome}</span></p></div></> : <div className="rounded-xl border bg-white p-7 text-sm text-slate-500">Appeal detail retrieval is not exposed by the current API.</div>; }
