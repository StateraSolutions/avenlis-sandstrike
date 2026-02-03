import React, { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  IconButton,
  Tooltip,
  Tabs,
  Tab
} from '@mui/material'
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  History as HistoryIcon,
  Assessment as ResultsIcon,
} from '@mui/icons-material'
import { formatDateTime } from '../utils/dateFormat'
import SlideOverlay from '../components/common/SlideOverlay'
import axios from 'axios'

interface Session {
  id: string
  name: string
  target: string
  status: string
  source?: string
  created_at?: string
  updated_at?: string
  total_prompts?: number
  passed_probes?: number
  failed_probes?: number
  error_probes?: number
  target_url?: string
  target_model?: string
  grader?: string
  results?: PromptResult[]
}

interface PromptResult {
  id?: string
  prompt_id: string
  status: 'pass' | 'fail' | 'error' | 'passed' | 'failed'
  response: string
  attack_technique?: string
  vuln_category?: string
  vuln_subcategory?: string
  severity?: string
  prompt?: string
  grader_verdict?: string
  grader_confidence?: string
}

interface Prompt {
  id: string
  attack_technique: string
  vulnerability_category: string
  vulnerability_subcategory: string
  prompt_text: string
}

interface SessionDetails {
  session: Session
  results: PromptResult[]
  prompts: Prompt[]
}

interface Target {
  id: string
  name: string
  ip_address?: string
  target?: string
}

const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [selectedSession, setSelectedSession] = useState<SessionDetails | null>(null)
  const [overlayTab, setOverlayTab] = useState(0)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [hoveredRow, setHoveredRow] = useState<string | null>(null)
  const [selectedResult, setSelectedResult] = useState<PromptResult | null>(null)
  const [targets, setTargets] = useState<Target[]>([])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter) params.append('status', statusFilter)
      
      const response = await axios.get(`/api/sessions?${params.toString()}`)
      const sessionsData = response.data.sessions || response.data || []
      console.log('Loaded sessions:', sessionsData.length, sessionsData)
      setSessions(sessionsData)
    } catch (error) {
      console.error('Failed to load sessions:', error)
      if (axios.isAxiosError(error)) {
        console.error('Response:', error.response?.data)
      }
    } finally {
      setLoading(false)
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) return
    
    try {
      await axios.delete(`/api/sessions/${sessionId}`)
      await loadSessions() // Reload sessions after deletion
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session')
    }
  }

  const viewSession = async (session: Session) => {
    setLoadingDetails(true)
    try {
      // Load session details from the correct endpoint
      const [sessionResponse, promptsResponse] = await Promise.all([
        axios.get(`/api/sessions/${session.id}`),
        axios.get('/api/prompts') // Load all prompts to match with results
      ])

      const sessionData = sessionResponse.data.session
      setSelectedSession({
        session: sessionData,
        results: sessionData.results || [],
        prompts: promptsResponse.data.prompts || []
      })
      setOverlayTab(0) // Reset to first tab
    } catch (error) {
      console.error('Failed to load session details:', error)
      alert('Failed to load session details')
    } finally {
      setLoadingDetails(false)
    }
  }

  const loadTargets = async () => {
    try {
      const response = await axios.get('/api/targets')
      setTargets(response.data.targets || [])
    } catch (error) {
      console.error('Failed to load targets:', error)
    }
  }

  const getTargetName = (targetUrl?: string): string => {
    if (!targetUrl) return 'Unknown'
    // Try to find matching target by ip_address or target field
    const matchingTarget = targets.find(
      t => t.ip_address === targetUrl || t.target === targetUrl
    )
    return matchingTarget?.name || targetUrl
  }

  useEffect(() => {
    loadSessions()
    loadTargets()
  }, [statusFilter, sourceFilter])

  // Filter sessions based on all filters
  const filteredSessions = sessions.filter(session => {
    // Search term filter (name or target)
    const sessionName = session.name || session.session_name || ''
    const sessionTarget = session.target || session.target_url || ''
    const matchesSearch = !searchTerm || 
      sessionName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sessionTarget.toLowerCase().includes(searchTerm.toLowerCase())
    
    // Status filter
    const matchesStatus = !statusFilter || session.status === statusFilter
    
    // Source filter
    const matchesSource = !sourceFilter || 
      (sourceFilter === 'file' && session.source === 'file') ||
      (sourceFilter === 'local' && session.source !== 'file')
    
    return matchesSearch && matchesStatus && matchesSource
  })

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success'
      case 'running': return 'warning'
      case 'failed': return 'error'
      case 'pending': return 'default'
      case 'pass': return 'success'
      case 'passed': return 'success'
      case 'fail': return 'error'
      case 'error': return 'error'
      default: return 'default'
    }
  }

  const formatStatusText = (status: string) => {
    if (!status) return 'Unknown'
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
  }

  const formatGraderName = (grader?: string) => {
    if (!grader) return 'Unknown'
    const graderLower = grader.toLowerCase()
    if (graderLower === 'avenlis_copilot') {
      return 'Avenlis Copilot Grader'
    } else if (graderLower === 'ollama') {
      return 'Ollama'
    } else if (graderLower === 'openai') {
      return 'OpenAI'
    } else if (graderLower === 'gemini') {
      return 'Gemini'
    }
    // Default: capitalize first letter and replace underscores with spaces
    return grader
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  return (
    <Box>
      {/* Page Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Test Sessions
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            View and manage your test sessions
          </Typography>
        </Box>
        <Button
          variant="outlined"
          onClick={loadSessions}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <RefreshIcon />}
        >
          Refresh
        </Button>
      </Box>

      {/* Summary Stats */}
      {!loading && filteredSessions.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Box display="grid" gridTemplateColumns="repeat(4, 1fr)" gap={3}>
              <Box textAlign="center">
                <Typography variant="h3" fontWeight="bold" color="primary.main">
                  {filteredSessions.length}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                  Total Sessions
                </Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h3" fontWeight="bold" color="success.main">
                  {filteredSessions.filter(s => s.status === 'completed').length}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                  Completed
                </Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h3" fontWeight="bold" color="warning.main">
                  {filteredSessions.filter(s => s.status === 'running').length}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                  Running
                </Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h3" fontWeight="bold" color="error.main">
                  {filteredSessions.filter(s => s.status === 'failed').length}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                  Failed
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <TextField
              placeholder="Search sessions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 300 }}
            />
            
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
               <Select
                 value={statusFilter}
                 label="Status"
                 onChange={(e) => setStatusFilter(e.target.value)}
               >
                 <MenuItem value="">All Status</MenuItem>
                 <MenuItem value="completed">Completed</MenuItem>
                 <MenuItem value="running">Running</MenuItem>
                 <MenuItem value="failed">Failed</MenuItem>
               </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Source</InputLabel>
              <Select
                value={sourceFilter}
                label="Source"
                onChange={(e) => setSourceFilter(e.target.value)}
              >
                <MenuItem value="">All Sources</MenuItem>
                <MenuItem value="file">File</MenuItem>
                <MenuItem value="local">Local</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ flex: 1 }} />

            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                setSearchTerm('')
                setStatusFilter('')
                setSourceFilter('')
              }}
              sx={{ minWidth: 100 }}
            >
              Clear Filters
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Sessions Table */}
      <Card>
        <CardContent>
          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : filteredSessions.length === 0 ? (
            <Box 
              display="flex" 
              flexDirection="column" 
              alignItems="center" 
              justifyContent="center"
              py={8}
            >
              <HistoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" textAlign="center">
                No sessions found
              </Typography>
              <Typography variant="body2" color="textSecondary" textAlign="center" mt={1}>
                {sessions.length === 0 ? 'Start a new scan to create your first session' : 'Try adjusting your filters'}
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Session Name</TableCell>
                    <TableCell>Target</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Total Prompts</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredSessions.map((session, index) => (
                    <TableRow 
                      key={session.id} 
                      sx={{
                        cursor: 'pointer',
                        backgroundColor: hoveredRow === session.id ? '#f5f5f5' : (index % 2 === 0 ? 'white' : '#f8f9fa'),
                        '&:hover': {
                          backgroundColor: '#f5f5f5'
                        }
                      }}
                      onMouseEnter={() => setHoveredRow(session.id)}
                      onMouseLeave={() => setHoveredRow(null)}
                      onClick={() => viewSession(session)}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {session.name || session.session_name || 'Unnamed Session'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" className="text-ellipsis" title={session.target || session.target_url || ''}>
                          {session.target || session.target_url || ''}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={formatStatusText(session.status || 'Unknown')}
                          size="small"
                          color={getStatusColor(session.status) as any}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={session.source === 'file' ? 'File' : 'Local'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {session.results?.length || session.total_prompts || 0}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {session.created_at ? formatDateTime(session.created_at) : 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box 
                          display="flex" 
                          gap={1}
                          sx={{
                            opacity: hoveredRow === session.id ? 1 : 0,
                            transition: 'opacity 0.2s ease'
                          }}
                        >
                          <Tooltip title="View Details">
                            <IconButton 
                              size="small" 
                              color="primary"
                              onClick={(e) => {
                                e.stopPropagation()
                                viewSession(session)
                              }}
                              disabled={loadingDetails}
                            >
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {session.source !== 'file' && (
                            <Tooltip title="Delete Session">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  deleteSession(session.id)
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>


      {/* Session Details Overlay */}
      <SlideOverlay
        open={!!selectedSession}
        onClose={() => setSelectedSession(null)}
        title={
          selectedSession ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h6" fontWeight="bold" noWrap>
                {selectedSession.session.name}
              </Typography>
              <Chip
                label={formatStatusText(selectedSession.session.status)}
                color={getStatusColor(selectedSession.session.status) as any}
                size="small"
              />
            </Box>
          ) : undefined
        }
        width={800}
      >
        {selectedSession && (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3, pt: 2 }}>
              <Tabs value={overlayTab} onChange={(_, newValue) => setOverlayTab(newValue)}>
                <Tab label="Overview" icon={<HistoryIcon />} iconPosition="start" />
                <Tab label="Results" icon={<ResultsIcon />} iconPosition="start" />
              </Tabs>
            </Box>

            {/* Tab Content */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              {overlayTab === 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Session Overview
                  </Typography>
                  
                  <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
                      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Session ID
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {selectedSession.session.id}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Target
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {getTargetName(selectedSession.session.target_url || selectedSession.session.target)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Model
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {selectedSession.session.target_model || 'Unknown'}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Created
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {selectedSession.session.created_at 
                              ? formatDateTime(selectedSession.session.created_at)
                              : 'Unknown'
                            }
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Source
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {selectedSession.session.source || 'Local'}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Grader Used
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {formatGraderName(selectedSession.session.grader)}
                          </Typography>
                        </Box>
                      </Box>
          </CardContent>
        </Card>

                  <Typography variant="h6" gutterBottom>
                    Test Summary
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2 }}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="primary.main" fontWeight="bold">
                          {selectedSession.session.total_prompts || selectedSession.results.length}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Total Prompts
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main" fontWeight="bold">
                          {selectedSession.session.passed_probes || 
                           selectedSession.results.filter(r => {
                             const status = r.status?.toLowerCase()
                             return status === 'pass' || status === 'passed'
                           }).length}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Passed
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="error.main" fontWeight="bold">
                          {selectedSession.session.failed_probes || 
                           selectedSession.results.filter(r => {
                             const status = r.status?.toLowerCase()
                             return status === 'fail' || status === 'failed'
                           }).length}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Failed
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="warning.main" fontWeight="bold">
                          {selectedSession.session.error_probes || 
                           selectedSession.results.filter(r => r.status === 'error').length}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Errors
                        </Typography>
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              )}

              {overlayTab === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Test Results
                  </Typography>
                  
                  {selectedSession.results.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <ResultsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="body1" color="textSecondary">
                        No results available for this session.
                      </Typography>
                    </Box>
                  ) : (
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Prompt ID</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Response</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {selectedSession.results.map((result, index) => (
                            <TableRow 
                              key={result.id || index}
                              sx={{
                                cursor: 'pointer',
                                '&:hover': {
                                  backgroundColor: '#f5f5f5'
                                }
                              }}
                              onClick={() => setSelectedResult(result)}
                            >
                              <TableCell>
                                <Typography variant="body2" fontFamily="monospace">
                                  {result.prompt_id}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={formatStatusText(result.status)}
                                  color={getStatusColor(result.status) as any}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>
                                <Typography 
                                  variant="body2" 
                                  sx={{ 
                                    maxWidth: 200,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}
                                  title={result.response}
                                >
                                  {result.response}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </Box>
              )}
            </Box>
          </Box>
        )}
      </SlideOverlay>

      {/* Prompt Result Details Overlay */}
      <SlideOverlay
        open={!!selectedResult}
        onClose={() => setSelectedResult(null)}
        title={`Prompt Details: ${selectedResult?.prompt_id || 'Unknown'}`}
        width={900}
      >
        {selectedResult && (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 3, pb: 6 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 3 }}>
              <Box>
                <Typography variant="caption" color="textSecondary">
                  Prompt ID
                </Typography>
                <Typography variant="body1" fontWeight="medium" fontFamily="monospace">
                  {selectedResult.prompt_id}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="textSecondary">
                  Status
                </Typography>
                <Box sx={{ mt: 0.5 }}>
                  <Chip
                    label={formatStatusText(selectedResult.status)}
                    color={getStatusColor(selectedResult.status) as any}
                    size="small"
                  />
                </Box>
              </Box>
              {selectedResult.attack_technique && (
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    Attack Technique
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {selectedResult.attack_technique.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                  </Typography>
                </Box>
              )}
              {selectedResult.vuln_category && (
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    Vulnerability Category
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {selectedResult.vuln_category.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                  </Typography>
                </Box>
              )}
              {selectedResult.vuln_subcategory && (
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    Vulnerability Subcategory
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {selectedResult.vuln_subcategory.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                  </Typography>
                </Box>
              )}
              {selectedResult.severity && (
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    Severity
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {selectedResult.severity.charAt(0).toUpperCase() + selectedResult.severity.slice(1)}
                  </Typography>
                </Box>
              )}
            </Box>

            {selectedResult.prompt && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Prompt Text
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                    {selectedResult.prompt}
                  </Typography>
                </Paper>
              </Box>
            )}

            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Target Response
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                  {selectedResult.response}
                </Typography>
              </Paper>
            </Box>

            {(selectedResult.grader_verdict || selectedResult.grader_confidence) && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Grader Assessment
                </Typography>
                <Card variant="outlined">
                  <CardContent>
                    {selectedResult.grader_verdict && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          Verdict
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {selectedResult.grader_verdict}
                        </Typography>
                      </Box>
                    )}
                    {selectedResult.grader_confidence && (
                      <Box>
                        <Typography variant="caption" color="textSecondary">
                          Confidence
                        </Typography>
                        <Typography variant="body2" fontWeight="medium" sx={{ mt: 0.5 }}>
                          {selectedResult.grader_confidence}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        )}
      </SlideOverlay>
    </Box>
  )
}

export default Sessions
