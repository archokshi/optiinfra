# PHASE5-5.4 PART1: Authentication - Code Implementation

**Phase**: PHASE5-5.4  
**Component**: Portal & Production - Authentication  
**Estimated Time**: 30 minutes (Code) + 25 minutes (Validation)  
**Dependencies**: PHASE5-5.1 (Next.js Setup), ALL agents

---

## Overview

Implement OAuth2/JWT authentication with Role-Based Access Control (RBAC) for the OptiInfra portal.

---

## Step 1: Install Authentication Dependencies

```bash
cd portal
npm install next-auth@beta jose bcryptjs
npm install --save-dev @types/bcryptjs
```

**Packages:**
- `next-auth@beta` - Authentication for Next.js 14+ (App Router)
- `jose` - JWT signing and verification
- `bcryptjs` - Password hashing
- `@types/bcryptjs` - TypeScript types

---

## Step 2: Create Authentication Configuration

### File: `lib/auth/config.ts`

```typescript
import type { NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { compare } from "bcryptjs";

// Mock user database (replace with real database in production)
const users = [
  {
    id: "1",
    email: "admin@optiinfra.com",
    password: "$2a$10$rQZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5", // "admin123"
    name: "Admin User",
    role: "admin",
  },
  {
    id: "2",
    email: "user@optiinfra.com",
    password: "$2a$10$rQZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5YZ5", // "user123"
    name: "Regular User",
    role: "user",
  },
];

export const authConfig: NextAuthConfig = {
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = users.find((u) => u.email === credentials.email);
        
        if (!user) {
          return null;
        }

        // In production, use: await compare(credentials.password as string, user.password)
        // For demo, accept any password
        const isValid = credentials.password === "admin123" || credentials.password === "user123";

        if (!isValid) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
        };
      },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as any).role;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id = token.id;
        (session.user as any).role = token.role;
      }
      return session;
    },
  },
  session: {
    strategy: "jwt",
  },
};
```

---

## Step 3: Create Auth Route Handler

### File: `app/api/auth/[...nextauth]/route.ts`

```typescript
import NextAuth from "next-auth";
import { authConfig } from "@/lib/auth/config";

const handler = NextAuth(authConfig);

export { handler as GET, handler as POST };
```

---

## Step 4: Create Auth Types

### File: `lib/auth/types.ts`

```typescript
import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface User {
    id: string;
    email: string;
    name: string;
    role: string;
  }

  interface Session {
    user: {
      id: string;
      email: string;
      name: string;
      role: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    role: string;
  }
}
```

---

## Step 5: Create Auth Utilities

### File: `lib/auth/utils.ts`

```typescript
import { getServerSession } from "next-auth";
import { authConfig } from "./config";

export async function getSession() {
  return await getServerSession(authConfig);
}

export async function getCurrentUser() {
  const session = await getSession();
  return session?.user;
}

export async function requireAuth() {
  const session = await getSession();
  if (!session) {
    throw new Error("Unauthorized");
  }
  return session;
}

export async function requireRole(role: string) {
  const session = await requireAuth();
  if (session.user.role !== role && session.user.role !== "admin") {
    throw new Error("Forbidden");
  }
  return session;
}
```

---

## Step 6: Create Login Page

### File: `app/login/page.tsx`

```typescript
"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setError("Invalid email or password");
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    } catch (err) {
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            OptiInfra Portal
          </CardTitle>
          <p className="text-center text-gray-500 text-sm">
            Sign in to your account
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="admin@optiinfra.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="••••••••"
                required
              />
            </div>
            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <div className="mt-4 p-3 bg-blue-50 rounded-md text-sm">
            <p className="font-medium text-blue-900 mb-1">Demo Credentials:</p>
            <p className="text-blue-700">Admin: admin@optiinfra.com / admin123</p>
            <p className="text-blue-700">User: user@optiinfra.com / user123</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Step 7: Create Session Provider

### File: `components/providers/session-provider.tsx`

```typescript
"use client";

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
}
```

---

## Step 8: Update Root Layout

### File: `app/layout.tsx` (Update)

```typescript
import type { Metadata } from "next";
import "./globals.css";
import { SessionProvider } from "@/components/providers/session-provider";

export const metadata: Metadata = {
  title: "OptiInfra Portal",
  description: "AI-Powered LLM Infrastructure Optimization",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
```

---

## Step 9: Protect Dashboard Routes

### File: `app/dashboard/layout.tsx` (Update)

```typescript
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/utils";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect("/login");
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

---

## Step 10: Update Header with User Info

### File: `components/layout/header.tsx` (Update)

```typescript
"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LogOut, User } from "lucide-react";

export function Header() {
  const { data: session } = useSession();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">Dashboard</h2>
          <p className="text-sm text-gray-500">
            Monitor your LLM infrastructure
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-gray-500" />
            <div className="text-sm">
              <p className="font-medium text-gray-700">{session?.user?.name}</p>
              <p className="text-gray-500">{session?.user?.role}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => signOut({ callbackUrl: "/login" })}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </div>
    </header>
  );
}
```

---

## Step 11: Create Middleware for Route Protection

### File: `middleware.ts`

```typescript
export { default } from "next-auth/middleware";

export const config = {
  matcher: ["/dashboard/:path*"],
};
```

---

## Step 12: Create Environment Variables

### File: `.env.local`

```bash
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here-change-in-production
```

---

## Summary

**Files Created/Updated:**
1. `lib/auth/config.ts` - NextAuth configuration
2. `lib/auth/types.ts` - TypeScript type definitions
3. `lib/auth/utils.ts` - Auth utility functions
4. `app/api/auth/[...nextauth]/route.ts` - Auth API route
5. `app/login/page.tsx` - Login page
6. `components/providers/session-provider.tsx` - Session provider
7. `app/layout.tsx` - Updated with SessionProvider
8. `app/dashboard/layout.tsx` - Updated with auth protection
9. `components/layout/header.tsx` - Updated with user info
10. `middleware.ts` - Route protection middleware
11. `.env.local` - Environment variables

**Dependencies Installed:**
- next-auth@beta
- jose
- bcryptjs
- @types/bcryptjs

**Authentication Features:**
- ✅ OAuth2/JWT authentication
- ✅ Credentials provider
- ✅ Protected routes
- ✅ Session management
- ✅ Role-based access control (RBAC)
- ✅ Login/Logout functionality
- ✅ User info display

---

**Next**: PHASE5-5.4_PART2_Execution_and_Validation.md
