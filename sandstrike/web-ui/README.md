# Avenlis SandStrike Web UI

Modern React-based web interface for Avenlis SandStrike, built with Vite, React Router, and Material-UI.

## 🚀 Features

- **Modern React Architecture**: Built with React 18, TypeScript, and Vite
- **Material-UI Design**: Consistent, professional UI components
- **Real-time Updates**: Socket.IO integration for live updates
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Multi-timezone Support**: Display dates in user's preferred timezone
- **Interactive Charts**: Visualize security metrics and trends

## 📁 Project Structure

```
avenlis/web-ui/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── layout/         # Layout components (Sidebar, etc.)
│   ├── contexts/           # React contexts (Socket, Timezone)
│   ├── pages/              # Main application pages
│   │   ├── Dashboard.tsx   # Security dashboard with metrics
│   │   ├── Sessions.tsx    # Test session management
│   │   ├── Collections.tsx # Prompt collection management
│   │   ├── Prompts.tsx     # Adversarial prompts library
│   │   ├── Settings.tsx    # Application settings
│   │   └── scan/          # Scanning interfaces
│   ├── App.tsx            # Main app component with routing
│   ├── main.tsx           # App entry point
│   └── index.css          # Global styles
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── index.html             # HTML template
```

## 🛠️ Development Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running Avenlis Python backend (on port 8080)

### Installation

1. **Navigate to the web-ui directory**:
   ```bash
   cd avenlis/web-ui
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to `http://localhost:3000`

### Available Scripts

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

## 🏗️ Architecture

### Frontend Stack
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript for better development experience
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing for single-page application
- **Material-UI**: Professional React component library
- **Recharts**: Interactive charts and data visualization
- **Socket.IO**: Real-time communication with backend

### API Integration
- **Axios**: HTTP client for API requests
- **Proxy Setup**: Vite dev server proxies API calls to Flask backend
- **Real-time Updates**: Socket.IO for live data updates

### Context Providers
- **SocketContext**: Manages Socket.IO connection and events
- **TimezoneContext**: Handles timezone selection and date formatting

## 🔄 Backend Integration

The React frontend communicates with the Flask backend through:

1. **REST API**: HTTP requests to `/api/*` endpoints
2. **Socket.IO**: Real-time updates and notifications
3. **Proxy Configuration**: Development server proxies requests to `localhost:8080`

### API Endpoints Used
- `GET /api/dashboard/metrics` - Security dashboard data
- `GET /api/sessions` - Test session listing
- `GET /api/collections` - Prompt collections
- `GET /api/prompts` - Adversarial prompts
- `GET /api/timezones` - Available timezones
- `POST /api/timezone` - Set user timezone
- `POST /api/wipe-local-data` - Data management

## 🎨 Theming and Styling

### Material-UI Theme
```tsx
const theme = createTheme({
  palette: {
    primary: { main: '#667eea' },      // Avenlis brand color
    secondary: { main: '#48bb78' },    // Success green
    background: { 
      default: '#f8fafc',             // Light gray background
      paper: '#ffffff'                // Card backgrounds
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
})
```

### Custom CSS Classes
- `.text-ellipsis` - Truncate long text with ellipsis
- `.text-muted` - Muted text color
- `.badge-*` - Status badges (success, error, warning, etc.)

## 📊 Pages Overview

### Dashboard (`/dashboard`)
- Security metrics overview
- Vulnerability statistics
- Interactive charts (Pie charts, Bar charts)
- Recent vulnerabilities table
- Quick action buttons

### Sessions (`/sessions`)
- List all test sessions
- Filter by status, target, search term
- Session details and management
- Delete local sessions
- Summary statistics

### Scan Pages (`/scan/*`)
- **Ollama** (`/scan/ollama`): Local Ollama model testing
- **HuggingFace** (`/scan/huggingface`): HuggingFace model testing
- **All Providers** (`/scan/providers`): Multi-provider testing

### Collections (`/collections`)
- Manage prompt collections
- Organize adversarial prompts
- Collection statistics

### Prompts (`/prompts`)
- Browse adversarial prompt library
- Detailed prompt overlays
- Encoding history and management (coming soon)

### Compliance Pages
- **MITRE ATLAS** (`/mitre-atlas`): ATLAS framework mapping
- **OWASP LLM** (`/owasp-llm`): OWASP Top 10 LLM mapping

### Settings (`/settings`)
- Timezone configuration
- Local data management
- Application information

## 🔧 Configuration

### Vite Configuration (`vite.config.ts`)
```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8080',      // API proxy
      '/socket.io': {                       // Socket.IO proxy
        target: 'http://localhost:8080',
        ws: true,
      }
    }
  }
})
```

### Environment Variables
No environment variables required for development. Production builds may require:
- `VITE_API_BASE_URL`: Backend API base URL

## 🚀 Production Deployment

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Serve static files**:
   The `dist/` folder contains production-ready static files that can be served by any web server.

3. **Backend Integration**:
   Ensure the Flask backend serves the React build files or configure reverse proxy.

## 🧪 Testing

Currently using the development setup for testing. Future plans include:
- Jest for unit testing
- React Testing Library for component testing
- Cypress for end-to-end testing

## 📝 Contributing

1. Follow the existing code structure and patterns
2. Use TypeScript for type safety
3. Follow Material-UI design principles
4. Ensure responsive design
5. Test with the Flask backend
6. Update documentation for new features

## 🔍 Troubleshooting

### Common Issues

**Frontend won't start**:
- Ensure Node.js 18+ is installed
- Check that port 3000 is available
- Run `npm install` to install dependencies

**API calls failing**:
- Ensure Flask backend is running on port 8080
- Check Vite proxy configuration
- Verify CORS settings in Flask backend

**Socket.IO connection issues**:
- Confirm backend Socket.IO is configured correctly
- Check browser network tab for connection errors
- Verify proxy configuration for WebSocket support

**Build errors**:
- Run `npm run build` to check for TypeScript errors
- Fix any linting issues with `npm run lint`
- Ensure all imports are properly typed

## 📚 References

- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Material-UI Documentation](https://mui.com/)
- [React Router Tutorial](https://reactrouter.com/en/main)
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)

---

**Built with ❤️ for Avenlis SandStrike**




