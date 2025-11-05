# PHASE5-5.1 PART2: Next.js Setup - Execution and Validation

**Phase**: PHASE5-5.1  
**Component**: Portal & Production  
**Objective**: Execute Next.js setup and validate the installation  
**Estimated Time**: 20 minutes  
**Prerequisites**: PART1 completed

---

## Execution Steps

### Step 1: Create Next.js Application (5 minutes)

```bash
# Navigate to project root
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra"

# Create portal directory
npx create-next-app@latest portal --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

**Expected Output:**
```
Creating a new Next.js app in C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\portal

Using npm.

Installing dependencies:
- react
- react-dom
- next

Installing devDependencies:
- typescript
- @types/react
- @types/node
- @types/react-dom
- tailwindcss
- postcss
- autoprefixer
- eslint
- eslint-config-next

Success! Created portal at C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\portal
```

---

### Step 2: Install Additional Dependencies (2 minutes)

```bash
cd portal

# Install utility libraries
npm install clsx tailwind-merge

# Verify installation
npm list
```

**Expected Output:**
```
optiinfra-portal@1.0.0
├── clsx@2.0.0
├── next@14.0.3
├── react@18.2.0
├── react-dom@18.2.0
└── tailwind-merge@2.1.0
```

---

### Step 3: Create Directory Structure (3 minutes)

```bash
# Create component directories
mkdir -p components/ui
mkdir -p components/layout
mkdir -p components/dashboard

# Create lib directory
mkdir -p lib

# Create dashboard routes
mkdir -p "app/(dashboard)/cost"
mkdir -p "app/(dashboard)/performance"
mkdir -p "app/(dashboard)/resource"
mkdir -p "app/(dashboard)/application"

# Create API routes
mkdir -p app/api/health

# Verify structure
tree /F
```

**Expected Structure:**
```
portal/
├── app/
│   ├── (dashboard)/
│   │   ├── cost/
│   │   ├── performance/
│   │   ├── resource/
│   │   └── application/
│   ├── api/
│   │   └── health/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── ui/
│   ├── layout/
│   └── dashboard/
├── lib/
├── public/
├── node_modules/
├── .env.example
├── .gitignore
├── next.config.js
├── package.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

---

### Step 4: Create Configuration Files (3 minutes)

**Create .env.example:**
```bash
# Copy from PART1 or create manually
notepad .env.example
```

**Create .env.local:**
```bash
# Copy from example
copy .env.example .env.local
```

**Verify files exist:**
```bash
dir .env*
```

---

### Step 5: Create Core Files (5 minutes)

**Create lib/types.ts:**
```bash
notepad lib\types.ts
# Copy content from PART1
```

**Create lib/api.ts:**
```bash
notepad lib\api.ts
# Copy content from PART1
```

**Create lib/utils.ts:**
```bash
notepad lib\utils.ts
# Copy content from PART1
```

**Create app/api/health/route.ts:**
```bash
notepad app\api\health\route.ts
# Copy content from PART1
```

---

### Step 6: Update Configuration Files (2 minutes)

**Update tailwind.config.ts:**
```bash
notepad tailwind.config.ts
# Replace with content from PART1
```

**Update app/layout.tsx:**
```bash
notepad app\layout.tsx
# Replace with content from PART1
```

**Update app/page.tsx:**
```bash
notepad app\page.tsx
# Replace with content from PART1
```

**Update app/globals.css:**
```bash
notepad app\globals.css
# Replace with content from PART1
```

---

## Validation Steps

### Step 1: Type Check (1 minute)

```bash
# Run TypeScript type checking
npm run type-check
```

**Expected Output:**
```
> optiinfra-portal@1.0.0 type-check
> tsc --noEmit

# No errors should appear
```

**✅ Success Criteria:**
- No TypeScript errors
- All types resolve correctly

---

### Step 2: Lint Check (1 minute)

```bash
# Run ESLint
npm run lint
```

**Expected Output:**
```
> optiinfra-portal@1.0.0 lint
> next lint

✔ No ESLint warnings or errors
```

**✅ Success Criteria:**
- No linting errors
- Code follows Next.js conventions

---

### Step 3: Start Development Server (2 minutes)

```bash
# Start the dev server
npm run dev
```

**Expected Output:**
```
> optiinfra-portal@1.0.0 dev
> next dev

  ▲ Next.js 14.0.3
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Ready in 2.5s
```

**✅ Success Criteria:**
- Server starts without errors
- Accessible at http://localhost:3000
- Hot reload working

---

### Step 4: Test Landing Page (1 minute)

**Open browser:**
```
http://localhost:3000
```

**Expected Display:**
- OptiInfra logo and title
- "AI-Powered LLM Infrastructure Optimization" subtitle
- "Go to Dashboard" button
- "API Health" button
- Three metric cards (50%, 3x, 4)

**✅ Success Criteria:**
- Page loads without errors
- All elements visible
- Styling applied correctly
- No console errors

---

### Step 5: Test Health API (1 minute)

**Open browser:**
```
http://localhost:3000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-26T17:30:00.000Z",
  "service": "optiinfra-portal",
  "version": "1.0.0"
}
```

**✅ Success Criteria:**
- Returns 200 OK
- JSON response correct
- Timestamp is current

---

### Step 6: Test TypeScript Imports (1 minute)

**Create test file:**
```bash
notepad test-imports.ts
```

**Content:**
```typescript
import { apiClient } from './lib/api';
import { formatCurrency, formatPercentage } from './lib/utils';
import type { Agent, DashboardData } from './lib/types';

// Test type checking
const agent: Agent = {
  agent_id: "test",
  agent_name: "Test Agent",
  agent_type: "cost",
  version: "1.0.0",
  status: "active",
  last_heartbeat: new Date().toISOString(),
  capabilities: [],
  host: "localhost",
  port: 8001
};

console.log(formatCurrency(1000));
console.log(formatPercentage(50));
```

**Run type check:**
```bash
npx tsc test-imports.ts --noEmit
```

**Expected:** No errors

**Clean up:**
```bash
del test-imports.ts
```

---

### Step 7: Test Hot Reload (1 minute)

**With dev server running:**

1. Open `app/page.tsx`
2. Change the title from "OptiInfra" to "OptiInfra Portal"
3. Save the file
4. Check browser - should auto-refresh

**✅ Success Criteria:**
- Changes appear immediately
- No page refresh needed
- No errors in console

**Revert change:**
```typescript
// Change back to "OptiInfra"
```

---

### Step 8: Test Build (2 minutes)

```bash
# Stop dev server (Ctrl+C)

# Build for production
npm run build
```

**Expected Output:**
```
> optiinfra-portal@1.0.0 build
> next build

  ▲ Next.js 14.0.3

   Creating an optimized production build ...
 ✓ Compiled successfully
 ✓ Linting and checking validity of types
 ✓ Collecting page data
 ✓ Generating static pages (5/5)
 ✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    1.2 kB          85 kB
├ ○ /api/health                          0 B                0 B
└ ○ /_not-found                          871 B          81.2 kB

○  (Static)  automatically rendered as static HTML
```

**✅ Success Criteria:**
- Build completes successfully
- No errors or warnings
- All pages generated
- Bundle size reasonable

---

## Verification Checklist

### ✅ Installation
- [ ] Next.js 14 installed
- [ ] TypeScript configured
- [ ] TailwindCSS configured
- [ ] Dependencies installed

### ✅ Project Structure
- [ ] Directory structure created
- [ ] All folders present
- [ ] Files organized correctly

### ✅ Configuration
- [ ] Environment variables set
- [ ] Tailwind config updated
- [ ] TypeScript config correct
- [ ] Next.js config valid

### ✅ Core Files
- [ ] Types defined (lib/types.ts)
- [ ] API client created (lib/api.ts)
- [ ] Utils created (lib/utils.ts)
- [ ] Health API working

### ✅ Development
- [ ] Dev server starts
- [ ] Hot reload works
- [ ] No TypeScript errors
- [ ] No linting errors

### ✅ Pages
- [ ] Landing page loads
- [ ] Styling applied
- [ ] Navigation works
- [ ] No console errors

### ✅ Build
- [ ] Production build succeeds
- [ ] All pages generated
- [ ] No build errors

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### Issue: TypeScript errors

**Solution:**
```bash
# Check tsconfig.json is correct
# Restart TypeScript server in VS Code
# Run: npm run type-check
```

### Issue: Tailwind styles not applying

**Solution:**
```bash
# Verify tailwind.config.ts content paths
# Check globals.css has @tailwind directives
# Restart dev server
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Use different port
PORT=3001 npm run dev

# Or kill existing process
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## Success Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Installation Time | < 5 min | ⏱️ |
| Build Time | < 30 sec | ⏱️ |
| Dev Server Start | < 5 sec | ⏱️ |
| Page Load Time | < 1 sec | ⏱️ |
| TypeScript Errors | 0 | ✅ |
| Linting Errors | 0 | ✅ |
| Console Errors | 0 | ✅ |

---

## Next Phase Preparation

**Before starting PHASE5-5.2:**

1. ✅ Ensure dev server is running
2. ✅ Verify all files created
3. ✅ Confirm no errors in console
4. ✅ Test hot reload working
5. ✅ Review project structure

**Ready for:**
- Dashboard layout implementation
- Agent status cards
- Metrics visualization
- Real-time updates

---

## Completion Summary

**What We Built:**
- ✅ Next.js 14 application with App Router
- ✅ TypeScript configuration
- ✅ TailwindCSS styling system
- ✅ API client infrastructure
- ✅ Type definitions
- ✅ Utility functions
- ✅ Landing page
- ✅ Health API endpoint

**What's Working:**
- Development server
- Hot module replacement
- TypeScript type checking
- ESLint validation
- Production builds
- API routes

**Ready For:**
- Dashboard components (PHASE5-5.2)
- Agent monitoring
- Real-time updates
- Chart integration

---

**PHASE5-5.1 Complete! Next.js foundation is ready for dashboard implementation.** 🚀

**Next Step:** PHASE5-5.2 - Dashboard Components
