# OptiInfra Portal

**Next.js 14 customer dashboard for OptiInfra**

## Overview

The Portal provides a modern web interface for:
- Viewing all agent status and metrics
- Cost, performance, resource, and application dashboards
- Approving/rejecting agent recommendations
- Viewing execution history
- Real-time updates via WebSocket

## Architecture

```
portal/
├── src/
│   ├── app/             # Next.js 14 app directory
│   ├── components/      # React components
│   ├── lib/             # Utilities and API clients
│   └── types/           # TypeScript types
├── public/
│   ├── images/
│   └── icons/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── Dockerfile
└── README.md
```

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Components**: shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **Real-time**: WebSocket
- **State**: React hooks + Context

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
cd portal
npm install
```

### Run locally
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build for production
```bash
npm run build
npm start
```

### Run tests
```bash
npm test
```

## Pages

- `/` - Overview dashboard
- `/cost` - Cost optimization dashboard
- `/performance` - Performance metrics dashboard
- `/resource` - Resource utilization dashboard
- `/application` - Application quality dashboard
- `/recommendations` - Pending recommendations
- `/history` - Execution history

## Configuration

Environment variables (`.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8080
```

## Deployment

See [Deployment Guide](../docs/DEPLOYMENT.md) for production deployment instructions.
