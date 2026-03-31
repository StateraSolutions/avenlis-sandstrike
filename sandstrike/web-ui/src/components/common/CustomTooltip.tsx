import React, { useState, useRef, useEffect } from 'react'
import { Box, Paper, Typography, Fade } from '@mui/material'
import { motion, AnimatePresence } from 'framer-motion'

interface CustomTooltipProps {
  title: string | React.ReactNode
  children: React.ReactElement
  placement?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
  maxWidth?: number
  arrow?: boolean
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  title,
  children,
  placement = 'top',
  delay = 500,
  maxWidth = 300,
  arrow = true
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const timeoutRef = useRef<NodeJS.Timeout>()
  const childRef = useRef<HTMLElement>()

  const showTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setIsVisible(false)
  }

  const updatePosition = () => {
    if (!childRef.current) return

    const rect = childRef.current.getBoundingClientRect()
    const scrollX = window.pageXOffset
    const scrollY = window.pageYOffset

    let x = rect.left + scrollX
    let y = rect.top + scrollY

    switch (placement) {
      case 'top':
        x += rect.width / 2
        y -= 10
        break
      case 'bottom':
        x += rect.width / 2
        y += rect.height + 10
        break
      case 'left':
        x -= 10
        y += rect.height / 2
        break
      case 'right':
        x += rect.width + 10
        y += rect.height / 2
        break
    }

    setPosition({ x, y })
  }

  useEffect(() => {
    if (isVisible) {
      updatePosition()
    }
  }, [isVisible, placement])

  const getTooltipStyle = () => {
    const baseStyle = {
      position: 'fixed' as const,
      zIndex: 2000,
      pointerEvents: 'none' as const,
      maxWidth
    }

    switch (placement) {
      case 'top':
        return {
          ...baseStyle,
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, -100%)'
        }
      case 'bottom':
        return {
          ...baseStyle,
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, 0%)'
        }
      case 'left':
        return {
          ...baseStyle,
          left: position.x,
          top: position.y,
          transform: 'translate(-100%, -50%)'
        }
      case 'right':
        return {
          ...baseStyle,
          left: position.x,
          top: position.y,
          transform: 'translate(0%, -50%)'
        }
    }
  }

  const getArrowStyle = () => {
    const arrowSize = 6
    const arrowStyle: React.CSSProperties = {
      position: 'absolute',
      width: 0,
      height: 0,
      borderStyle: 'solid'
    }

    switch (placement) {
      case 'top':
        return {
          ...arrowStyle,
          top: '100%',
          left: '50%',
          marginLeft: -arrowSize,
          borderWidth: `${arrowSize}px ${arrowSize}px 0 ${arrowSize}px`,
          borderColor: 'rgba(0, 0, 0, 0.87) transparent transparent transparent'
        }
      case 'bottom':
        return {
          ...arrowStyle,
          bottom: '100%',
          left: '50%',
          marginLeft: -arrowSize,
          borderWidth: `0 ${arrowSize}px ${arrowSize}px ${arrowSize}px`,
          borderColor: 'transparent transparent rgba(0, 0, 0, 0.87) transparent'
        }
      case 'left':
        return {
          ...arrowStyle,
          left: '100%',
          top: '50%',
          marginTop: -arrowSize,
          borderWidth: `${arrowSize}px 0 ${arrowSize}px ${arrowSize}px`,
          borderColor: 'transparent transparent transparent rgba(0, 0, 0, 0.87)'
        }
      case 'right':
        return {
          ...arrowStyle,
          right: '100%',
          top: '50%',
          marginTop: -arrowSize,
          borderWidth: `${arrowSize}px ${arrowSize}px ${arrowSize}px 0`,
          borderColor: 'transparent rgba(0, 0, 0, 0.87) transparent transparent'
        }
    }
  }

  const clonedChild = React.cloneElement(children, {
    ref: (el: HTMLElement) => {
      childRef.current = el
      if (typeof children.ref === 'function') {
        children.ref(el)
      } else if (children.ref) {
        children.ref.current = el
      }
    },
    onMouseEnter: (e: React.MouseEvent) => {
      showTooltip()
      if (children.props.onMouseEnter) {
        children.props.onMouseEnter(e)
      }
    },
    onMouseLeave: (e: React.MouseEvent) => {
      hideTooltip()
      if (children.props.onMouseLeave) {
        children.props.onMouseLeave(e)
      }
    }
  })

  return (
    <>
      {clonedChild}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
            style={getTooltipStyle()}
          >
            <Paper
              elevation={8}
              sx={{
                px: 1.5,
                py: 1,
                bgcolor: 'rgba(0, 0, 0, 0.87)',
                color: 'white',
                fontSize: '0.75rem',
                borderRadius: 1,
                position: 'relative'
              }}
            >
              {typeof title === 'string' ? (
                <Typography variant="caption" color="inherit">
                  {title}
                </Typography>
              ) : (
                title
              )}
              {arrow && <div style={getArrowStyle()} />}
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default CustomTooltip
