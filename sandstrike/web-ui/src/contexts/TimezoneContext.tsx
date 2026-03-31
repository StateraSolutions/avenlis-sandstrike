import React, { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'

interface TimezoneContextType {
  timezone: string
  setTimezone: (timezone: string) => Promise<void>
  formatDateTime: (date: Date | string) => string
  timezones: Array<{
    value: string
    label: string
    group: string
  }>
  isLoading: boolean
}

const TimezoneContext = createContext<TimezoneContextType | undefined>(undefined)

export const useTimezone = () => {
  const context = useContext(TimezoneContext)
  if (!context) {
    throw new Error('useTimezone must be used within a TimezoneProvider')
  }
  return context
}

interface TimezoneProviderProps {
  children: React.ReactNode
}

export const TimezoneProvider: React.FC<TimezoneProviderProps> = ({ children }) => {
  const [timezone, setTimezoneState] = useState('Asia/Singapore')
  const [timezones, setTimezones] = useState<Array<{
    value: string
    label: string
    group: string
  }>>([])
  const [isLoading, setIsLoading] = useState(true)

  const setTimezone = async (newTimezone: string) => {
    try {
      await axios.post('/api/timezone', { timezone: newTimezone })
      setTimezoneState(newTimezone)
    } catch (error) {
      console.error('Failed to set timezone:', error)
      throw error
    }
  }

  const formatDateTime = (date: Date | string) => {
    try {
      const dateObj = typeof date === 'string' ? new Date(date) : date
      return new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(dateObj)
    } catch (error) {
      console.error('Error formatting date:', error)
      return date.toString()
    }
  }

  useEffect(() => {
    const loadTimezones = async () => {
      try {
        const response = await axios.get('/api/timezones')
        setTimezones(response.data.timezones)
        setTimezoneState(response.data.current)
      } catch (error) {
        console.error('Failed to load timezones:', error)
        // Set default timezone list
        setTimezones([
          { value: 'UTC', label: 'UTC', group: 'Common' },
          { value: 'Asia/Singapore', label: 'Asia/Singapore', group: 'Common' },
          { value: 'US/Eastern', label: 'US/Eastern', group: 'Common' },
          { value: 'US/Pacific', label: 'US/Pacific', group: 'Common' },
        ])
        setTimezoneState('Asia/Singapore') // Set default timezone
      } finally {
        setIsLoading(false)
      }
    }

    loadTimezones()
  }, [])

  return (
    <TimezoneContext.Provider value={{
      timezone,
      setTimezone,
      formatDateTime,
      timezones,
      isLoading
    }}>
      {children}
    </TimezoneContext.Provider>
  )
}



