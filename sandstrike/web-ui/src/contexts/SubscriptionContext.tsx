import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react'
import axios from 'axios'

interface UserSubscription {
  subscriptionPlan: 'free' | 'plus' | 'pro'
  isPaidUser: boolean
  isLoading: boolean
  error: string | null
}

interface SubscriptionContextType {
  subscription: UserSubscription
  refreshSubscription: () => Promise<void>
  isProUser: boolean
  isPlusUser: boolean
  isFreeUser: boolean
  isReady: boolean
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined)

interface SubscriptionProviderProps {
  children: ReactNode
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const [subscription, setSubscription] = useState<UserSubscription>({
    subscriptionPlan: 'free',
    isPaidUser: false,
    isLoading: true,
    error: null
  })

  const [isReady, setIsReady] = useState(false)
  const didInitRef = useRef(false)

  const checkSubscriptionStatus = async (forceRefresh: boolean = false) => {
    try {
      setSubscription(prev => ({ ...prev, isLoading: true, error: null }))
      
      // Add refresh query parameter if forceRefresh is true to bypass cache
      const url = forceRefresh ? '/api/auth/status?refresh=true' : '/api/auth/status'
      const response = await axios.get(url)
      const subscriptionPlan = response.data.user?.subscriptionPlan || 'free'
      
      setSubscription({
        subscriptionPlan,
        isPaidUser: subscriptionPlan === 'plus' || subscriptionPlan === 'pro',
        isLoading: false,
        error: null
      })
    } catch (error) {
      console.error('Error checking subscription status:', error)
      setSubscription({
        subscriptionPlan: 'free',
        isPaidUser: false,
        isLoading: false,
        error: 'Failed to check subscription status'
      })
    } finally {
      setIsReady(true)
    }
  }

  const refreshSubscription = async () => {
    await checkSubscriptionStatus(true) // Force refresh to bypass cache
  }

  useEffect(() => {
    // React 18 StrictMode runs effects twice in dev; avoid double auth flips.
    if (didInitRef.current) return
    didInitRef.current = true
    checkSubscriptionStatus()
  }, [])

  const isProUser = subscription.subscriptionPlan === 'pro'
  const isPlusUser = subscription.subscriptionPlan === 'plus'
  const isFreeUser = subscription.subscriptionPlan === 'free'

  const value: SubscriptionContextType = {
    subscription,
    refreshSubscription,
    isProUser,
    isPlusUser,
    isFreeUser,
    isReady
  }

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  )
}

export const useSubscription = (): SubscriptionContextType => {
  const context = useContext(SubscriptionContext)
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider')
  }
  return context
}

