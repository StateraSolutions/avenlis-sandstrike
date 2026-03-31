import React from 'react'
import {
  Drawer,
  Box,
  IconButton,
  Typography,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material'
import { Close as CloseIcon } from '@mui/icons-material'
import { motion } from 'framer-motion'

interface SlideOverlayProps {
  open: boolean
  onClose: () => void
  title?: string | React.ReactNode
  width?: number | string
  children: React.ReactNode
  actions?: React.ReactNode
}

const SlideOverlay: React.FC<SlideOverlayProps> = ({
  open,
  onClose,
  title,
  width = 600,
  children,
  actions
}) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  
  const drawerWidth = isMobile ? '100%' : width

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          maxWidth: '100%',
          bgcolor: 'background.default',
          borderLeft: '1px solid',
          borderColor: 'divider'
        }
      }}
      ModalProps={{
        keepMounted: true // Better open performance on mobile
      }}
    >
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'tween', duration: 0.3 }}
        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      >
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            {title && (
              typeof title === 'string' ? (
                <Typography variant="h6" fontWeight="bold" noWrap>
                  {title}
                </Typography>
              ) : (
                title
              )
            )}
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {actions}
            <IconButton
              onClick={onClose}
              size="small"
              sx={{
                color: 'text.secondary',
                '&:hover': {
                  bgcolor: 'action.hover'
                }
              }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Content */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 0
          }}
        >
          {children}
        </Box>
      </motion.div>
    </Drawer>
  )
}

export default SlideOverlay
