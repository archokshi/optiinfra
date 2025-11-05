# OptiInfra Portal

Modern Next.js 14 dashboard for monitoring and managing OptiInfra's multi-agent LLM optimization platform.

## Features

- Modern UI with Next.js 14 App Router
- TypeScript for type safety
- TailwindCSS for styling
- Real-time agent monitoring
- WebSocket integration (coming soon)
- Dark mode support (coming soon)
- Responsive design

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp env.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
portal/
├── app/              # Next.js App Router pages
├── components/       # React components
├── lib/              # Utilities and API client
└── public/           # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

See `env.example` for required environment variables.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State**: React Hooks
- **API**: Fetch API

## License

Proprietary - OptiInfra
