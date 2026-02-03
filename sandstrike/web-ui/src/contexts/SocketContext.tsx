import React, { createContext, useContext, useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'

interface SocketContextType {
  socket: Socket | null
  isConnected: boolean
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false
})

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

interface SocketProviderProps {
  children: React.ReactNode
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Initialize socket connection to the Flask backend
    const socketInstance = io('http://localhost:8080', {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      forceNew: true
    })

    socketInstance.on('connect', () => {
      console.log('Connected to Avenlis server via Socket.IO')
      setIsConnected(true)
    })

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from Avenlis server')
      setIsConnected(false)
    })

    socketInstance.on('connect_error', (error) => {
      console.log('Socket connection error:', error)
      setIsConnected(false)
    })

    socketInstance.on('status', (data) => {
      console.log('Server status:', data)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.close()
    }
  }, [])

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  )
}



