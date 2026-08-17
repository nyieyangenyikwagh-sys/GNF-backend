"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";
import type { Claim, Patient, User } from "@/lib/types";

type AuthStore = { token: string | null; user: User | null; login: (token: string, user: User | null) => void; logout: () => void; isAuthenticated: () => boolean };
export const useAuthStore = create<AuthStore>()(persist((set, get) => ({ token: null, user: null, login: (token, user) => { localStorage.setItem("token", token); set({ token, user }); }, logout: () => { localStorage.removeItem("token"); set({ token: null, user: null }); }, isAuthenticated: () => !!get().token }), { name: "rcm-auth" }));

type PatientStore = { patients: Patient[]; loading: boolean; fetchPatients: () => Promise<void>; createPatient: (data: unknown) => Promise<unknown> };
export const usePatientsStore = create<PatientStore>((set) => ({ patients: [], loading: false, fetchPatients: async () => { set({ loading: true }); try { const { data } = await api.get("/patients"); set({ patients: Array.isArray(data) ? data : data.items || [] }); } finally { set({ loading: false }); } }, createPatient: async (data) => (await api.post("/patients", data)).data }));
type ClaimsStore = { claims: Claim[]; loading: boolean; fetchClaims: () => Promise<void>; submitClaim: (data: unknown) => Promise<Claim>; transitionStatus: (id: number, to_status: string, reason_code?: string) => Promise<Claim> };
export const useClaimsStore = create<ClaimsStore>((set) => ({ claims: [], loading: false, fetchClaims: async () => { set({ loading: true }); try { const { data } = await api.get("/claims"); set({ claims: Array.isArray(data) ? data : data.items || [] }); } finally { set({ loading: false }); } }, submitClaim: async (data) => (await api.post("/claims", data)).data, transitionStatus: async (id, to_status, reason_code) => (await api.post(`/claims/${id}/status`, { to_status, reason_code })).data }));
