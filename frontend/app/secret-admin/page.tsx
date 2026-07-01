"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SecretAdminPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/login");
  }, [router]);

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center text-dark-muted font-mono text-sm">
      Redirecting to secure administration portal...
    </div>
  );
}
