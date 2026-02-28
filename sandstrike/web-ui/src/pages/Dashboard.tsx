import React, { useEffect, useState } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
} from '@mui/material'
import {
  Assessment as TestIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { useSocket } from '../contexts/SocketContext'
import axios from 'axios'

interface DashboardMetrics {
  total_tests: number
  total_vulnerabilities: number
  passed_probes: number
  failed_probes: number
  error_probes: number
  security_score: number
  critical: number
  high: number
  medium: number
  low: number
  total_sessions: number
  file_sessions: number
  local_sessions: number
  total_prompts: number
  total_collections: number
  vulnerabilities: Array<{
    id: string
    session_id: string
    session_name: string
    attack_technique: string
    vuln_category: string
    vuln_subcategory?: string
    severity: string
    score: number
    prompt: string
    response: string
    date: string
  }>
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const navigate = useNavigate()
  const { socket } = useSocket()

  // Utility function to format text: capitalize first letter and replace underscores with spaces
  const formatText = (text: string | null | undefined): string => {
    if (!text) return 'N/A'
    return text
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  const getSecurityScoreColor = (score: number) => {
    if (score < 40) return '#e53e3e' // Red for < 40%
    if (score >= 40 && score < 70) return '#ed8936' // Orange for 40-69%
    return '#48bb78' // Green for >= 70%
  }

  const loadMetrics = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      const response = await axios.get('/api/dashboard/metrics')
      
      // Ensure all required fields are present with default values
      const data = response.data
      setMetrics({
        total_tests: data.total_tests ?? 0,
        total_vulnerabilities: data.total_vulnerabilities ?? 0,
        passed_probes: data.passed_probes ?? 0,
        failed_probes: data.failed_probes ?? 0,
        error_probes: data.error_probes ?? 0,
        security_score: data.security_score ?? 0,
        critical: data.critical ?? 0,
        high: data.high ?? 0,
        medium: data.medium ?? 0,
        low: data.low ?? 0,
        total_sessions: data.total_sessions ?? 0,
        file_sessions: data.file_sessions ?? 0,
        local_sessions: data.local_sessions ?? 0,
        total_prompts: data.total_prompts ?? 0,
        total_collections: data.total_collections ?? 0,
        vulnerabilities: data.vulnerabilities ?? []
      })
    } catch (error) {
      console.error('Failed to load dashboard metrics:', error)
      // Set default metrics if API fails
      setMetrics({
        total_tests: 0,
        total_vulnerabilities: 0,
        passed_probes: 0,
        failed_probes: 0,
        error_probes: 0,
        security_score: 100,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        total_sessions: 0,
        file_sessions: 0,
        local_sessions: 0,
        total_prompts: 0,
        total_collections: 0,
        vulnerabilities: []
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadMetrics()
  }, [])

  useEffect(() => {
    if (socket) {
      // Listen for session updates to refresh metrics
      socket.on('session_created', () => {
        console.log('Session created, refreshing dashboard metrics')
        loadMetrics()
      })
      socket.on('session_updated', () => {
        console.log('Session updated, refreshing dashboard metrics')
        loadMetrics()
      })
      socket.on('session_deleted', () => {
        console.log('Session deleted, refreshing dashboard metrics')
        loadMetrics()
      })
      
      return () => {
        socket.off('session_created')
        socket.off('session_updated')
        socket.off('session_deleted')
      }
    }
  }, [socket])

  // Auto-refresh metrics every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadMetrics()
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="60vh">
        <CircularProgress />
      </Box>
    )
  }

  if (!metrics) {
    return (
      <Box textAlign="center" py={8}>
        <Typography variant="h6" color="textSecondary">
          Failed to load dashboard metrics
        </Typography>
        <Button
          variant="contained"
          onClick={() => loadMetrics()}
          sx={{ mt: 2 }}
          startIcon={<RefreshIcon />}
        >
          Retry
        </Button>
      </Box>
    )
  }

  const severityData = [
    { name: 'Critical', value: metrics.critical, color: '#e53e3e' },
    { name: 'High', value: metrics.high, color: '#8b0000' },
    { name: 'Medium', value: metrics.medium, color: '#ff8c00' },
    { name: 'Low', value: metrics.low, color: '#87ceeb' }
  ].filter(item => item.value > 0)

  const testResultsData = [
    { name: 'Passed', value: metrics.passed_probes, color: '#48bb78' },
    { name: 'Failed', value: metrics.failed_probes, color: '#8b0000' },
    { name: 'Error', value: metrics.error_probes, color: '#ff8c00' }
  ].filter(item => item.value > 0)


  const getTopAttackTechniques = () => {
    // Count attack techniques from vulnerabilities
    const techniqueCounts: { [key: string]: number } = {}
    
    if (metrics?.vulnerabilities) {
      metrics.vulnerabilities.forEach(vuln => {
        const technique = vuln.attack_technique || 'Unknown'
        techniqueCounts[technique] = (techniqueCounts[technique] || 0) + 1
      })
    }
    
    // Convert to array and sort by count
    const techniques = Object.entries(techniqueCounts)
      .map(([technique, count]) => {
        const formattedTechnique = formatText(technique)
        return {
          technique: formattedTechnique.length > 30 ? formattedTechnique.substring(0, 30) + '...' : formattedTechnique,
          count,
          percentage: metrics?.vulnerabilities ? Math.round((count / metrics.vulnerabilities.length) * 100) : 0
        }
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 10) // Top 10 techniques
    
    return techniques
  }

  const hasNoData =
    Number(metrics.total_tests || 0) === 0 &&
    Number(metrics.total_sessions || 0) === 0 &&
    Number(metrics.total_vulnerabilities || 0) === 0 &&
    (metrics.vulnerabilities?.length || 0) === 0

  const getTopVulnerabilityCategories = () => {
    // Count vulnerability categories from vulnerabilities
    const categoryCounts: { [key: string]: number } = {}
    
    if (metrics?.vulnerabilities) {
      metrics.vulnerabilities.forEach(vuln => {
        const category = vuln.vuln_category || 'Unknown'
        categoryCounts[category] = (categoryCounts[category] || 0) + 1
      })
    }
    
    // Convert to array and sort by count
    const categories = Object.entries(categoryCounts)
      .map(([category, count]) => {
        const formattedCategory = formatText(category)
        return {
          category: formattedCategory.length > 25 ? formattedCategory.substring(0, 25) + '...' : formattedCategory,
          count,
          percentage: metrics?.vulnerabilities ? Math.round((count / metrics.vulnerabilities.length) * 100) : 0
        }
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 8) // Top 8 categories
    
    return categories
  }

  return (
    <Box>
      {/* Page Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Security Dashboard
            </Typography>
            {refreshing && (
              <CircularProgress size={20} sx={{ color: 'primary.main' }} />
            )}
          </Box>
          <Typography variant="subtitle1" color="textSecondary">
            Monitor your LLM security posture and vulnerabilities
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            onClick={() => navigate('/scan')}
            startIcon={<TestIcon />}
          >
            Run Scan
          </Button>
          <Button
            variant="outlined"
            onClick={() => loadMetrics(true)}
            disabled={refreshing}
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </Box>

      {/* Empty State: Welcome and Get Started */}
      {hasNoData && (
        <Card
          sx={{
            mb: 4,
            p: 4,
            textAlign: 'center',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
            border: '1px dashed #cbd5e1',
          }}
        >
          <CardContent sx={{ py: 6, px: 4 }}>
            <Typography variant="h5" fontWeight="bold" color="text.primary" gutterBottom sx={{ mb: 2 }}>
              Welcome to SandStrike
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 480, mx: 'auto' }}>
              You haven&apos;t run any security scans yet. Start by running your first scan against an LLM target to discover vulnerabilities and assess your security posture.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/scan')}
              startIcon={<TestIcon />}
              sx={{
                px: 4,
                py: 1.5,
                fontSize: '1rem',
                textTransform: 'none',
                fontWeight: 600,
              }}
            >
              Get Started — Run Your First Scan
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics Cards - Reorganized */}
      <Grid container spacing={3} mb={4}>
        {/* Column 1: Security Score + Vulnerabilities */}
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', mb: 2 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h4" fontWeight="bold" color={getSecurityScoreColor(metrics.security_score)} gutterBottom>
                {metrics.security_score}%
              </Typography>
              <Typography variant="body2" color="#718096">
                Security Score
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h4" fontWeight="bold" color="#e53e3e" gutterBottom>
                {metrics.total_vulnerabilities.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="#718096">
                Vulnerabilities
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Column 2: Top Attack Techniques */}
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Top Attack Techniques
              </Typography>
              <Box sx={{ flex: 1, maxHeight: 500, overflowY: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 120 }}>
                {getTopAttackTechniques().length > 0 ? (
                  getTopAttackTechniques().map((item, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, width: '100%' }}>
                      <Typography variant="body2" sx={{ flex: 1, mr: 2 }}>
                        {item.technique}
                      </Typography>
                      <Typography variant="body2" fontWeight="bold" color="primary">
                        {item.count}
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No data yet
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Column 3: Top Vulnerability Categories */}
        <Grid item xs={12} sm={6} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="h6" gutterBottom>
                Top Vulnerability Categories
              </Typography>
              <Box sx={{ flex: 1, maxHeight: 500, overflowY: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 120 }}>
                {getTopVulnerabilityCategories().length > 0 ? (
                  getTopVulnerabilityCategories().map((item, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, width: '100%' }}>
                      <Typography variant="body2" sx={{ flex: 1, mr: 2 }}>
                        {item.category}
                      </Typography>
                      <Typography variant="body2" fontWeight="bold" color="primary">
                        {item.count}
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No data yet
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and Detailed Metrics */}
      <Grid container spacing={3} mb={4}>
        {/* Prompt Testing Statuses Chart */}
        {testResultsData.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Prompt Test Results
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={testResultsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis 
                        tickFormatter={(value) => Math.round(value).toString()}
                        domain={[0, 'dataMax']}
                        allowDecimals={false}
                      />
                      <Tooltip 
                        formatter={(value) => [Math.round(Number(value)), 'Count']}
                      />
                      <Bar dataKey="value" fill="#8884d8">
                        {testResultsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Vulnerability Severity Chart */}
        {severityData.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Failed Prompts by Severity
                </Typography>
                <Box height={300}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={severityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {severityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>



    </Box>
  )
}

export default Dashboard



