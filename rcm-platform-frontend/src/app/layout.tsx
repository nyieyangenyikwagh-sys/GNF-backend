import type { Metadata } from "next";
import "./globals.css";
import ProtectedRoute from "@/components/Auth/ProtectedRoute";
import Shell from "@/components/Layout/Shell";
export const metadata: Metadata = { title: "Alberta RCM | Health Claims", description: "Healthcare claims operations" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><ProtectedRoute><Shell>{children}</Shell></ProtectedRoute></body></html>; }
