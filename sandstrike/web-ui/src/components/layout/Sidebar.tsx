import React, { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useSubscription } from '../../contexts/SubscriptionContext'
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Typography,
  Tooltip
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  GpsFixed as TargetIcon,
  History as HistoryIcon,
  FolderOpen as FolderOpenIcon,
  Chat as ChatIcon,
  Security as SecurityIcon,
  Shield as ShieldIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Star as StarIcon,
  Help as HelpIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material'

const SIDEBAR_WIDTH = 280

interface NavItem {
  id: string
  label: string
  icon: React.ReactElement
  path?: string
  children?: NavItem[]
}

const navigationItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
        icon: <DashboardIcon />,
        path: '/dashboard'
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: <AssessmentIcon />,
    path: '/reports'
  }
]

const testingItems: NavItem[] = [
  {
    id: 'scan',
    label: 'Run Scan',
    icon: <TargetIcon />,
    path: '/scan'
  },
  {
    id: 'sessions',
    label: 'Sessions',
    icon: <HistoryIcon />,
    path: '/sessions'
  },
  {
    id: 'collections',
    label: 'Collections',
    icon: <FolderOpenIcon />,
    path: '/collections'
  },
  {
    id: 'prompts',
    label: 'Prompts',
    icon: <ChatIcon />,
    path: '/prompts'
  },
  {
    id: 'targets',
    label: 'Targets',
    icon: <TargetIcon />,
    path: '/targets'
  }
]

const complianceItems: NavItem[] = [
  {
    id: 'mitre-atlas',
    label: 'MITRE ATLAS Navigator',
    icon: <SecurityIcon />,
    path: '/mitre-atlas'
  },
  {
    id: 'owasp-llm',
    label: 'OWASP LLM Top 10',
    icon: <ShieldIcon />,
    path: '/owasp-llm'
  }
]

const Sidebar: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { isProUser, isPlusUser, isFreeUser } = useSubscription()
  const [expanded, setExpanded] = useState<string[]>(['dashboard'])
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsRef = useRef<HTMLDivElement>(null)

  const handleExpand = (itemId: string) => {
    setExpanded(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  const handleNavigation = (path: string) => {
    navigate(path)
    // Close settings submenu when navigating to any page
    setSettingsOpen(false)
  }

  const handleSettingsToggle = () => {
    setSettingsOpen(!settingsOpen)
  }

  const isActiveRoute = (path: string) => {
    return location.pathname === path
  }

  // Close settings submenu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsOpen && settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setSettingsOpen(false)
      }
    }

    if (settingsOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [settingsOpen])

  const renderNavItem = (item: NavItem, isDisabled: boolean = false) => {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expanded.includes(item.id)
    const isActive = item.path ? isActiveRoute(item.path) : false
    const isReportsDisabled = item.id === 'reports' && isDisabled

    return (
      <React.Fragment key={item.id}>
        <ListItem disablePadding>
          {isReportsDisabled ? (
            <Tooltip
              title={
                <Box>
                  <Typography variant="body2" component="span">
                    Requires Avenlis Pro,{' '}
                    <Typography
                      component="a"
                      href="https://staterasolv.com/pricing"
                      target="_blank"
                      rel="noopener noreferrer"
                      variant="body2"
                      sx={{
                        color: '#ffffff',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        '&:hover': {
                          color: '#e0e0e0'
                        }
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                    >
                      find out more
                    </Typography>
                  </Typography>
                </Box>
              }
              arrow
              placement="right"
            >
              <Box sx={{ width: '100%' }}>
                <ListItemButton
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                  }}
                  sx={{
                    py: 1.5,
                    px: 2,
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    backgroundColor: 'transparent',
                    opacity: 0.5,
                    cursor: 'not-allowed',
                    '&:hover': {
                      backgroundColor: 'transparent',
                    },
                  }}
                >
                  <ListItemIcon sx={{ 
                    color: 'rgba(255, 255, 255, 0.3)', 
                    minWidth: 40 
                  }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.label} 
                    sx={{ 
                      color: 'rgba(255, 255, 255, 0.3)',
                      '& .MuiTypography-root': {
                        fontWeight: 400
                      }
                    }} 
                  />
                </ListItemButton>
              </Box>
            </Tooltip>
          ) : (
            <ListItemButton
              onClick={() => {
                if (hasChildren) {
                  handleExpand(item.id)
                } else if (item.path) {
                  handleNavigation(item.path)
                }
              }}
              sx={{
                py: 1.5,
                px: 2,
                borderRadius: 1,
                mx: 1,
                mb: 0.5,
                backgroundColor: isActive ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: isActive ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <ListItemIcon sx={{ 
                color: '#ffffff', 
                minWidth: 40 
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.label} 
                sx={{ 
                  color: '#ffffff',
                  '& .MuiTypography-root': {
                    fontWeight: isActive ? 600 : 400
                  }
                }} 
              />
              {hasChildren && (
                isExpanded ? <ExpandLess sx={{ color: '#ffffff' }} /> : <ExpandMore sx={{ color: '#ffffff' }} />
              )}
            </ListItemButton>
          )}
        </ListItem>
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children?.map((child) => (
                <ListItem key={child.id} disablePadding>
                  <ListItemButton
                    onClick={() => child.path && handleNavigation(child.path)}
                    sx={{
                      py: 1,
                      px: 2,
                      pl: 5,
                      borderRadius: 1,
                      mx: 1,
                      mb: 0.5,
                      backgroundColor: child.path && isActiveRoute(child.path) ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
                      '&:hover': {
                        backgroundColor: child.path && isActiveRoute(child.path) ? 'rgba(102, 126, 234, 0.15)' : 'rgba(255, 255, 255, 0.1)',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ color: '#ffffff', minWidth: 32 }}>
                      {child.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={child.label} 
                      sx={{ 
                        color: '#ffffff',
                        '& .MuiTypography-root': {
                          fontSize: '0.875rem',
                          fontWeight: child.path && isActiveRoute(child.path) ? 600 : 400
                        }
                      }} 
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    )
  }

  const SectionHeader: React.FC<{ title: string }> = ({ title }) => (
    <Typography
      variant="caption"
      sx={{
        color: '#ffffff',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        px: 3,
        py: 1,
        mt: 2,
        display: 'block',
        opacity: 0.8
      }}
    >
      {title}
    </Typography>
  )

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: SIDEBAR_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: '#18727a',
          color: '#ffffff',
          borderRight: 'none',
        },
      }}
    >
      {/* Logo */}
      <Box sx={{ p: 0, textAlign: 'center', borderBottom: '1px solid rgba(255, 255, 255, 0.2)' }}>
        <img 
          src="/api/static/sandstrike_white.png" 
          alt="Avenlis SandStrike" 
          style={{ 
            height: '100px',
            width: 'auto',
            objectFit: 'contain'
          }}
        />
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 1 }}>
        <List>
          {navigationItems.map(item => renderNavItem(item, item.id === 'reports' && !isProUser))}
        </List>

        <SectionHeader title="Testing" />
        <List>
          {testingItems.map(item => renderNavItem(item))}
        </List>

        <SectionHeader title="Compliance" />
        <List>
          {complianceItems.map(item => renderNavItem(item))}
        </List>
      </Box>

      {/* Bottom Navigation */}
      <Box sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.2)', pt: 2 }} ref={settingsRef}>
        <List>
          <ListItem disablePadding>
            <ListItemButton
              onClick={handleSettingsToggle}
              sx={{
                py: 1.5,
                px: 2,
                borderRadius: 1,
                mx: 1,
                mb: 1,
                backgroundColor: settingsOpen ? 'rgba(255, 255, 255, 0.2)' : 'transparent',
                '&:hover': {
                  backgroundColor: settingsOpen ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <ListItemIcon sx={{ color: '#ffffff', minWidth: 40 }}>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText 
                primary="Settings" 
                sx={{ 
                  color: '#ffffff',
                  '& .MuiTypography-root': {
                    fontWeight: settingsOpen ? 600 : 400
                  }
                }} 
              />
              {settingsOpen ? <ExpandLess sx={{ color: '#ffffff' }} /> : <ExpandMore sx={{ color: '#ffffff' }} />}
            </ListItemButton>
          </ListItem>
          
          {/* Settings Submenu */}
          <Collapse in={settingsOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => window.open('https://avenlis.staterasolv.com/', '_blank')}
                  sx={{
                    py: 1,
                    px: 4,
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: '#ffffff', minWidth: 40 }}>
                    <StarIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary={isProUser ? "Manage Subscription" : "Upgrade Plan"} 
                    sx={{ 
                      color: '#ffffff',
                      '& .MuiTypography-root': {
                        fontWeight: 400,
                        fontSize: '0.9rem'
                      }
                    }} 
                  />
                </ListItemButton>
              </ListItem>
              
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => window.open('https://discord.com/invite/FzYTgxM5Db', '_blank')}
                  sx={{
                    py: 1,
                    px: 4,
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: '#ffffff', minWidth: 40 }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                    </svg>
                  </ListItemIcon>
                  <ListItemText 
                    primary="Join our Discord" 
                    sx={{ 
                      color: '#ffffff',
                      '& .MuiTypography-root': {
                        fontWeight: 400,
                        fontSize: '0.9rem'
                      }
                    }} 
                  />
                </ListItemButton>
              </ListItem>
              
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => window.open('https://docs.staterasolv.com/', '_blank')}
                  sx={{
                    py: 1,
                    px: 4,
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: '#ffffff', minWidth: 40 }}>
                    <HelpIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Documentation" 
                    sx={{ 
                      color: '#ffffff',
                      '& .MuiTypography-root': {
                        fontWeight: 400,
                        fontSize: '0.9rem'
                  }
                }} 
              />
            </ListItemButton>
          </ListItem>
              
              {/* Version and Plan Info */}
              <Box sx={{ px: 4, py: 2, borderTop: '1px solid rgba(255, 255, 255, 0.2)', mt: 1 }}>
                <Typography 
                  variant="body2" 
                  color="textSecondary" 
                  sx={{ 
                    fontSize: '0.75rem',
                    color: 'rgba(255, 255, 255, 0.7)',
                    mb: 0.5
                  }}
                >
                  Version 1.0.0
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontSize: '0.75rem',
                    color: isProUser ? '#48bb78' : isPlusUser ? '#4299e1' : '#ffffff',
                    fontWeight: isProUser || isPlusUser ? 600 : 400
                  }}
                >
                  {isProUser ? 'Pro Plan' : isPlusUser ? 'Plus Plan' : 'Free Plan'}
                </Typography>
              </Box>
            </List>
          </Collapse>
        </List>
      </Box>
    </Drawer>
  )
}

export default Sidebar



