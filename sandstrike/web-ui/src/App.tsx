import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Sidebar from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Scan from './pages/Scan'
import Sessions from './pages/Sessions'
import Collections from './pages/Collections'
import Prompts from './pages/Prompts'
import Targets from './pages/Targets'
import MitreAtlas from './pages/MitreAtlas'
import OwaspLlm from './pages/OwaspLlm'
import Reports from './pages/Reports'
import { SocketProvider } from './contexts/SocketContext'
import { SubscriptionProvider } from './contexts/SubscriptionContext'

function App() {
  return (
    <SocketProvider>
      <SubscriptionProvider>
          <Box sx={{ display: 'flex', height: '100vh' }}>
            <Sidebar />
            <Box 
              component="main" 
              sx={{ 
                flexGrow: 1, 
                px: 4,
                py: 3,
                overflow: 'auto',
                backgroundColor: 'background.default'
              }}
            >
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/scan" element={<Scan />} />
                <Route path="/sessions" element={<Sessions />} />
                <Route path="/collections" element={<Collections />} />
                <Route path="/prompts" element={<Prompts />} />
                <Route path="/targets" element={<Targets />} />
                <Route path="/mitre-atlas" element={<MitreAtlas />} />
                <Route path="/owasp-llm" element={<OwaspLlm />} />
                <Route path="/reports" element={<Reports />} />
              </Routes>
            </Box>
          </Box>
        </SubscriptionProvider>
    </SocketProvider>
  )
}

export default App



