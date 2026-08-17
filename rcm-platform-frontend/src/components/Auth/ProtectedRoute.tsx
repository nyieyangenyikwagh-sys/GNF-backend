"use client";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
export default function ProtectedRoute({ children }: { children: React.ReactNode }) { const router = useRouter(); const path = usePathname(); const token = useAuthStore((s) => s.token); useEffect(() => { if (!token && !path.startsWith("/auth")) router.replace("/auth/login"); }, [token, path, router]); if (!token && !path.startsWith("/auth")) return <main className="grid min-h-screen place-items-center">Checking your session…</main>; return <>{children}</>; }
