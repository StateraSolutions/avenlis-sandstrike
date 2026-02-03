import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Checkbox,
  FormControlLabel,
  IconButton,
  Chip,
  Fade,
  ClickAwayListener
} from '@mui/material'
import {
  KeyboardArrowDown as ArrowDownIcon,
  Close as CloseIcon
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

export interface DropdownOption {
  value: string
  label: string
  disabled?: boolean
}

interface CustomDropdownProps {
  options: DropdownOption[]
  selectedValues: string[]
  onChange: (values: string[]) => void
  placeholder?: string
  maxWidth?: number
  disabled?: boolean
  label?: string
}

const CustomDropdown: React.FC<CustomDropdownProps> = ({
  options,
  selectedValues,
  onChange,
  placeholder = 'Select options...',
  maxWidth = 400,
  disabled = false,
  label
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleToggle = (value: string) => {
    const newSelected = selectedValues.includes(value)
      ? selectedValues.filter(v => v !== value)
      : [...selectedValues, value]
    onChange(newSelected)
  }

  const handleRemoveChip = (value: string, event: React.MouseEvent) => {
    event.stopPropagation()
    onChange(selectedValues.filter(v => v !== value))
  }

  const getDisplayText = () => {
    if (selectedValues.length === 0) return placeholder
    if (selectedValues.length === 1) {
      const option = options.find(o => o.value === selectedValues[0])
      return option?.label || selectedValues[0]
    }
    return `${selectedValues.length} selected`
  }

  const handleClickAway = () => {
    setIsOpen(false)
    setSearchTerm('')
  }

  return (
    <ClickAwayListener onClickAway={handleClickAway}>
      <Box sx={{ position: 'relative', width: '100%', maxWidth }}>
        {label && (
          <Typography variant="caption" color="textSecondary" sx={{ mb: 0.5, display: 'block' }}>
            {label}
          </Typography>
        )}
        
        <Paper
          ref={dropdownRef}
          elevation={isOpen ? 2 : 1}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            minHeight: 40,
            bgcolor: disabled ? 'action.disabledBackground' : 'background.paper',
            border: '1px solid',
            borderColor: isOpen ? 'primary.main' : 'divider',
            '&:hover': {
              borderColor: disabled ? 'divider' : 'text.primary'
            }
          }}
          onClick={() => !disabled && setIsOpen(!isOpen)}
        >
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 0.5, overflow: 'hidden' }}>
            {selectedValues.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxWidth: '100%' }}>
                {selectedValues.slice(0, 3).map(value => {
                  const option = options.find(o => o.value === value)
                  return (
                    <Chip
                      key={value}
                      label={option?.label || value}
                      size="small"
                      onDelete={(e) => handleRemoveChip(value, e)}
                      deleteIcon={<CloseIcon />}
                      sx={{ 
                        maxWidth: 120,
                        '& .MuiChip-label': {
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }
                      }}
                    />
                  )
                })}
                {selectedValues.length > 3 && (
                  <Chip
                    label={`+${selectedValues.length - 3} more`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            ) : (
              <Typography
                variant="body2"
                color="textSecondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {getDisplayText()}
              </Typography>
            )}
          </Box>
          
          <IconButton
            size="small"
            sx={{
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease'
            }}
          >
            <ArrowDownIcon />
          </IconButton>
        </Paper>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 9999 }}
            >
              <Paper
                elevation={8}
                sx={{
                  mt: 0.5,
                  maxHeight: 400,
                  overflow: 'auto',
                  border: '1px solid',
                  borderColor: 'divider'
                }}
              >
                {filteredOptions.length === 0 ? (
                  <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="textSecondary">
                      No options available
                    </Typography>
                  </Box>
                ) : (
                  filteredOptions.map(option => (
                    <Box
                      key={option.value}
                      sx={{
                        '&:hover': {
                          bgcolor: 'action.hover'
                        }
                      }}
                    >
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedValues.includes(option.value)}
                            onChange={() => handleToggle(option.value)}
                            disabled={option.disabled}
                            size="small"
                          />
                        }
                        label={
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              maxWidth: 300
                            }}
                          >
                            {option.label}
                          </Typography>
                        }
                        sx={{
                          margin: 0,
                          padding: '4px 12px',
                          width: '100%',
                          '&:hover': {
                            bgcolor: 'action.hover'
                          }
                        }}
                      />
                    </Box>
                  ))
                )}
              </Paper>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    </ClickAwayListener>
  )
}

export default CustomDropdown
