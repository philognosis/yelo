# Bloom Dashboard

AI-Powered Performance Evaluation System - Next.js Dashboard

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

### 3. Open in Browser
```
http://localhost:3000/login
```

### 4. Login with Demo Accounts

The dashboard runs in **demo mode** by default (no backend required).

#### Quick Login - Click on Any Demo Role Card:
- **Employee** (`employee@example.com`) - View and complete evaluations
- **Manager** (`manager@example.com`) - Manage team evaluations with AI assistance
- **HR Admin** (`hr@example.com`) - Oversee cycles and system settings
- **Committee** (`committee@example.com`) - Review and calibrate evaluations

#### Manual Login:
- **Email**: Any of the emails above
- **Password**: `demo-password`

## Demo Mode vs Real API

### Demo Mode (Default)
- Uses mock authentication (no backend needed)
- All demo accounts work out of the box
- Perfect for exploring the UI and features
- Configured via `.env.local` with `NEXT_PUBLIC_DEMO_MODE=true`

### Connect to Real Backend API
1. Set `NEXT_PUBLIC_DEMO_MODE=false` in `.env.local`
2. Ensure backend API is running at `http://localhost:8000`
3. Restart dev server: `npm run dev`

## Available Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with Framer Motion
- **Authentication**: JWT with mock/real API support
- **State Management**: React Context API

## Project Structure

```
apps/bloom/dashboard/
├── app/                    # Next.js app directory
│   ├── dashboard/         # Dashboard pages
│   ├── employee/          # Employee views
│   ├── manager/           # Manager views
│   ├── hr/                # HR admin views
│   ├── committee/         # Committee views
│   └── login/             # Login page
├── components/            # Reusable UI components
├── contexts/              # React contexts (Auth, Theme)
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities and helpers
│   ├── api-client.ts     # API client
│   ├── mock-auth.ts      # Mock authentication
│   └── auth.ts           # Auth utilities
├── styles/               # Global styles
│   └── globals.css       # Tailwind + custom styles
└── types/                # TypeScript type definitions
```

## Features

- ✅ Role-based authentication (Employee, Manager, HR, Committee)
- ✅ Performance evaluation management
- ✅ AI-assisted evaluation drafting
- ✅ Peer review system
- ✅ Committee calibration
- ✅ Analytics and reporting
- ✅ Real-time notifications
- ✅ Dark/Light theme support
- ✅ Responsive design

## Environment Variables

See `.env.local` for configuration options.

## Troubleshooting

### Login Issues
- Ensure you're using the correct demo credentials
- Check browser console for errors
- Clear browser cache and localStorage if needed

### Build Issues
- Delete `.next` folder and rebuild: `rm -rf .next && npm run build`
- Check Node.js version (requires 18+)

### Connection Errors
- If seeing API connection errors, ensure demo mode is enabled in `.env.local`
- Set `NEXT_PUBLIC_DEMO_MODE=true`

## License

MIT
