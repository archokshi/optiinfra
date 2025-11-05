# PHASE5-5.4 PART2: Authentication - Execution and Validation

**Phase**: PHASE5-5.4  
**Component**: Portal & Production - Authentication  
**Estimated Time**: 25 minutes  
**Prerequisites**: PHASE5-5.4_PART1 completed

---

## Execution Steps

### Step 1: Install Dependencies

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\portal
npm install next-auth@beta jose bcryptjs
npm install --save-dev @types/bcryptjs
```

**Expected Output:**
```
added 3 packages
```

---

### Step 2: Create Directory Structure

```bash
# Create auth directories
mkdir -p lib\auth
mkdir -p app\api\auth\[...nextauth]
mkdir -p app\login
mkdir -p components\providers
```

---

### Step 3: Create Authentication Configuration Files

Create the following files in order:

1. **lib/auth/config.ts** - Copy from PART1
2. **lib/auth/types.ts** - Copy from PART1
3. **lib/auth/utils.ts** - Copy from PART1
4. **app/api/auth/[...nextauth]/route.ts** - Copy from PART1

---

### Step 4: Create Login Page

Create **app/login/page.tsx** - Copy from PART1

---

### Step 5: Create Session Provider

Create **components/providers/session-provider.tsx** - Copy from PART1

---

### Step 6: Update Root Layout

Update **app/layout.tsx** - Copy from PART1

---

### Step 7: Update Dashboard Layout

Update **app/dashboard/layout.tsx** - Copy from PART1

---

### Step 8: Update Header Component

Update **components/layout/header.tsx** - Copy from PART1

---

### Step 9: Create Middleware

Create **middleware.ts** in root directory - Copy from PART1

---

### Step 10: Create Environment Variables

Create **.env.local** in root directory:

```bash
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=optiinfra-secret-key-change-in-production-2025
```

---

### Step 11: Start Development Server

```bash
npm run dev
```

**Expected Output:**
```
▲ Next.js 16.0.0 (Turbopack)
- Local:        http://localhost:3000
✓ Ready in 3s
```

---

## Validation Steps

### Test 1: Login Page Access

1. **Navigate to**: http://localhost:3000/login
2. **Expected**: Login page displays with:
   - OptiInfra Portal title
   - Email and password fields
   - Sign In button
   - Demo credentials box

**✅ Pass Criteria**: Login page loads successfully

---

### Test 2: Dashboard Redirect (Unauthenticated)

1. **Navigate to**: http://localhost:3000/dashboard
2. **Expected**: Automatically redirects to `/login`

**✅ Pass Criteria**: Unauthenticated users cannot access dashboard

---

### Test 3: Admin Login

1. **Go to**: http://localhost:3000/login
2. **Enter**:
   - Email: `admin@optiinfra.com`
   - Password: `admin123`
3. **Click**: Sign In
4. **Expected**: Redirects to `/dashboard`

**✅ Pass Criteria**: Admin can log in successfully

---

### Test 4: User Info Display

1. **After logging in**, check header
2. **Expected**: Header shows:
   - User icon
   - Name: "Admin User"
   - Role: "admin"
   - Sign Out button

**✅ Pass Criteria**: User information displays correctly

---

### Test 5: Session Persistence

1. **After logging in**, refresh the page
2. **Expected**: Still logged in, no redirect to login

**✅ Pass Criteria**: Session persists across page refreshes

---

### Test 6: Sign Out

1. **Click**: Sign Out button in header
2. **Expected**: 
   - Redirects to `/login`
   - Session cleared

**✅ Pass Criteria**: Sign out works correctly

---

### Test 7: Invalid Credentials

1. **Go to**: http://localhost:3000/login
2. **Enter**:
   - Email: `wrong@example.com`
   - Password: `wrongpass`
3. **Click**: Sign In
4. **Expected**: Error message "Invalid email or password"

**✅ Pass Criteria**: Invalid credentials rejected

---

### Test 8: Regular User Login

1. **Go to**: http://localhost:3000/login
2. **Enter**:
   - Email: `user@optiinfra.com`
   - Password: `user123`
3. **Click**: Sign In
4. **Expected**: 
   - Redirects to `/dashboard`
   - Header shows "Regular User" and role "user"

**✅ Pass Criteria**: Regular user can log in

---

### Test 9: Protected Routes

Test all dashboard routes while logged in:

1. http://localhost:3000/dashboard ✅
2. http://localhost:3000/dashboard/cost ✅
3. http://localhost:3000/dashboard/performance ✅
4. http://localhost:3000/dashboard/resource ✅
5. http://localhost:3000/dashboard/application ✅
6. http://localhost:3000/dashboard/settings ✅

**✅ Pass Criteria**: All routes accessible when authenticated

---

### Test 10: Middleware Protection

1. **Sign out**
2. **Try to access**: http://localhost:3000/dashboard/cost
3. **Expected**: Redirects to `/login`

**✅ Pass Criteria**: Middleware protects all dashboard routes

---

## Verification Checklist

- [ ] Dependencies installed successfully
- [ ] All files created in correct locations
- [ ] Login page displays correctly
- [ ] Unauthenticated users redirected to login
- [ ] Admin login works
- [ ] User login works
- [ ] Invalid credentials rejected
- [ ] User info displays in header
- [ ] Session persists across refreshes
- [ ] Sign out works
- [ ] All dashboard routes protected
- [ ] Middleware working correctly

---

## Troubleshooting

### Issue: "Module not found: next-auth"

**Solution:**
```bash
npm install next-auth@beta --force
```

### Issue: "NEXTAUTH_SECRET is not set"

**Solution:**
- Ensure `.env.local` exists in root directory
- Restart dev server after creating `.env.local`

### Issue: Redirect loop

**Solution:**
- Check `NEXTAUTH_URL` matches your dev server URL
- Clear browser cookies
- Restart dev server

### Issue: Session not persisting

**Solution:**
- Check browser allows cookies
- Verify `.env.local` has `NEXTAUTH_SECRET`
- Clear browser cache

---

## Expected File Structure

```
portal/
├── .env.local                              ✅
├── middleware.ts                           ✅
├── app/
│   ├── layout.tsx                          ✅ (updated)
│   ├── login/
│   │   └── page.tsx                        ✅
│   ├── dashboard/
│   │   └── layout.tsx                      ✅ (updated)
│   └── api/
│       └── auth/
│           └── [...nextauth]/
│               └── route.ts                ✅
├── components/
│   ├── layout/
│   │   └── header.tsx                      ✅ (updated)
│   └── providers/
│       └── session-provider.tsx            ✅
└── lib/
    └── auth/
        ├── config.ts                       ✅
        ├── types.ts                        ✅
        └── utils.ts                        ✅
```

---

## Success Criteria

✅ **Authentication System Working**
- Login page functional
- Protected routes working
- Session management active
- User info displaying
- Sign out functional

✅ **Security Implemented**
- JWT tokens used
- Middleware protecting routes
- Credentials validated
- Sessions encrypted

✅ **User Experience**
- Smooth login flow
- Clear error messages
- Demo credentials provided
- Persistent sessions

---

## Performance Metrics

- **Login Time**: < 1 second
- **Page Load (Authenticated)**: < 500ms
- **Session Check**: < 100ms
- **Sign Out**: < 500ms

---

## Next Steps

After validation:
1. ✅ Mark PHASE5-5.4 as complete
2. 📝 Create PHASE5-5.4_COMPLETE.md
3. 🚀 Proceed to PHASE5-5.5 Kubernetes Deployment

---

## Demo Credentials

**Admin Account:**
- Email: admin@optiinfra.com
- Password: admin123
- Role: admin

**User Account:**
- Email: user@optiinfra.com
- Password: user123
- Role: user

---

**Status**: Ready for execution ✅
