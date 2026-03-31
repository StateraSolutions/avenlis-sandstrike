import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
  Tabs,
  Tab,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material'
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Add as AddIcon,
  ContentCopy as CopyIcon,
  Security as SecurityIcon,
  Chat as ChatIcon
} from '@mui/icons-material'
import axios from 'axios'
import { CopyToClipboard } from 'react-copy-to-clipboard'
import SlideOverlay from '../components/common/SlideOverlay'
import CustomTooltip from '../components/common/CustomTooltip'
import { useSocket } from '../contexts/SocketContext'

interface Prompt {
  id: string
  attack_technique: string
  vuln_category: string
  vuln_subcategory: string | null
  prompt: string
  created_at?: string
  updated_at?: string
  usage_count?: number
  success_rate?: number
  mitreatlasmapping?: string[]
  owasp_top10_llm_mapping?: string[]
  severity?: string
  collection_id?: string
  source?: string
}

interface PromptDetails {
  prompt: Prompt
  usageHistory: any[]
  relatedSessions: any[]
}

const Prompts: React.FC = () => {
  const navigate = useNavigate()
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [subcategoryFilter, setSubcategoryFilter] = useState('')
  const [techniqueFilter, setTechniqueFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [selectedPrompt, setSelectedPrompt] = useState<PromptDetails | null>(null)
  const [overlayTab, setOverlayTab] = useState(0)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [hoveredRow, setHoveredRow] = useState<string | null>(null)
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null)
  const [copiedPromptId, setCopiedPromptId] = useState<string | null>(null)
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const { socket } = useSocket()

  // Utility function to format text: capitalize first letter and replace underscores with spaces
  const formatText = (text: string | null | undefined): string => {
    if (!text) return 'N/A'
    return text
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  // Form state for creating/editing prompts
  const [formData, setFormData] = useState({
    id: '',
    attack_technique: '',
    vulnerability_category: '',
    vulnerability_subcategory: '',
    severity: '',
    prompt_text: '',
    source: 'local', // 'local' or 'file'
    target_file: '' // filename when source is 'file'
  })

  // Available prompt files
  const [availableFiles, setAvailableFiles] = useState<string[]>([])
  const [newFileMode, setNewFileMode] = useState(false)
  const [newFileName, setNewFileName] = useState('')

  useEffect(() => {
    loadPrompts()
    loadAvailableFiles()
  }, [])

  useEffect(() => {
    if (socket) {
      socket.on('prompt_updated', loadPrompts)
      socket.on('prompt_created', loadPrompts)
      socket.on('prompt_deleted', loadPrompts)
      return () => {
        socket.off('prompt_updated', loadPrompts)
        socket.off('prompt_created', loadPrompts)
        socket.off('prompt_deleted', loadPrompts)
      }
    }
  }, [socket])

  const loadPrompts = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/prompts')
      setPrompts(response.data.prompts || [])
    } catch (error) {
      console.error('Failed to load prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableFiles = async () => {
    try {
      const response = await axios.get('/api/prompts/files')
      setAvailableFiles(response.data.files || [])
    } catch (error) {
      console.error('Failed to load available files:', error)
      // Set default files if API fails
      setAvailableFiles(['adversarial_prompts.yaml'])
    }
  }

  const viewPrompt = async (prompt: Prompt) => {
    try {
      // Load prompt usage data
      const usageResponse = await axios.get(`/api/prompts/${prompt.id}/usage`)
      const usageData = usageResponse.data
      
      // Update prompt with usage statistics
      const promptWithUsage = {
        ...prompt,
        usage_count: usageData.usage_count || 0,
        success_rate: usageData.success_rate || 0
      }

      setSelectedPrompt({
        prompt: promptWithUsage,
        usageHistory: usageData.sessions || [],
        relatedSessions: usageData.sessions || []
      })
      setOverlayTab(0)
    } catch (error) {
      console.error('Failed to load prompt details:', error)
      setSelectedPrompt({
        prompt: {
          ...prompt,
          usage_count: 0,
          success_rate: 0
        },
        usageHistory: [],
        relatedSessions: []
      })
    }
  }

  const deletePrompt = async (promptId: string) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return
    
    try {
      await axios.delete(`/api/prompts/${promptId}`)
      await loadPrompts()
    } catch (error) {
      console.error('Failed to delete prompt:', error)
      alert('Failed to delete prompt')
    }
  }

  const handleCopyPrompt = (promptId: string) => {
    setCopiedPromptId(promptId)
    setSnackbarOpen(true)
    setTimeout(() => setCopiedPromptId(null), 2000)
  }

  const openCreateModal = () => {
    setFormData({
      id: '',
      attack_technique: '',
      vulnerability_category: '',
      vulnerability_subcategory: '',
      severity: '',
      prompt_text: '',
      source: 'local',
      target_file: ''
    })
    setNewFileMode(false)
    setNewFileName('')
    setEditingPrompt(null)
    setCreateModalOpen(true)
  }

  const openEditModal = (prompt: Prompt) => {
    setFormData({
      id: prompt.id,
      attack_technique: prompt.attack_technique,
      vulnerability_category: prompt.vuln_category,
      vulnerability_subcategory: prompt.vuln_subcategory || '',
      severity: prompt.severity || '',
      prompt_text: prompt.prompt,
      source: prompt.source || 'local',
      target_file: ''
    })
    setEditingPrompt(prompt)
    setCreateModalOpen(true)
  }

  const handleSavePrompt = async () => {
    try {
      const payload = {
        ...formData,
        // Normalize field names expected by backend
        vuln_category: formData.vulnerability_category,
        vuln_subcategory: formData.vulnerability_subcategory,
        severity: formData.severity
      }

      // Auto-generate ID if left empty
      const trimmedId = (payload.id || '').trim()
      payload.id = trimmedId || `newPrompt_${Date.now()}`

      if (payload.source === 'file') {
        const rawTarget = newFileMode ? newFileName.trim() : payload.target_file.trim()
        const sanitized = rawTarget.endsWith('.yaml') ? rawTarget : `${rawTarget}.yaml`
        payload.target_file = sanitized
      }

      if (editingPrompt) {
        // Update existing prompt
        await axios.put(`/api/prompts/${editingPrompt.id}`, payload)
      } else {
        // Create new prompt
        await axios.post('/api/prompts', payload)
      }
      setCreateModalOpen(false)
      await loadPrompts()
    } catch (error) {
      console.error('Failed to save prompt:', error)
      alert('Failed to save prompt')
    }
  }

  // Filter prompts based on search and filters
  const filteredPrompts = prompts.filter(prompt => {
    const matchesSearch = 
      prompt.prompt.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesCategory = !categoryFilter || prompt.vuln_category === categoryFilter
    const matchesSubcategory = !subcategoryFilter || prompt.vuln_subcategory === subcategoryFilter
    const matchesTechnique = !techniqueFilter || prompt.attack_technique === techniqueFilter
    const matchesSource = !sourceFilter || prompt.source === sourceFilter
    
    return matchesSearch && matchesCategory && matchesSubcategory && matchesTechnique && matchesSource
  })

  const getUniqueCategories = () => {
    return Array.from(new Set(prompts.map(p => p.vuln_category).filter(Boolean)))
  }

  const getUniqueSubcategories = () => {
    return Array.from(new Set(prompts.map(p => p.vuln_subcategory).filter((s): s is string => Boolean(s))))
  }

  const getUniqueTechniques = () => {
    return Array.from(new Set(prompts.map(p => p.attack_technique).filter(Boolean)))
  }


  return (
    <Box>
      <Box mb={4} display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
            Adversarial Prompts
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Browse and manage your adversarial prompts
        </Typography>
      </Box>
        <Button
          variant="outlined"
          onClick={loadPrompts}
          startIcon={<RefreshIcon />}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" sx={{ overflowX: 'auto', flexWrap: 'nowrap', pb: 1 }}>
            <TextField
              placeholder="Search prompts..."
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
            
            
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Attack Technique</InputLabel>
              <Select
                value={techniqueFilter}
                label="Attack Technique"
                onChange={(e) => setTechniqueFilter(e.target.value)}
              >
                <MenuItem value="">All Techniques</MenuItem>
                {getUniqueTechniques().map(technique => (
                  <MenuItem key={technique} value={technique}>
                    {technique}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel>Vulnerability Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Vulnerability Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="">All Categories</MenuItem>
                {getUniqueCategories().map(category => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel>Vulnerability Subcategory</InputLabel>
              <Select
                value={subcategoryFilter}
                label="Vulnerability Subcategory"
                onChange={(e) => setSubcategoryFilter(e.target.value)}
              >
                <MenuItem value="">All Subcategories</MenuItem>
                {getUniqueSubcategories().map(subcategory => (
                  <MenuItem key={subcategory} value={subcategory}>
                    {subcategory}
                  </MenuItem>
                ))}
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
                setCategoryFilter('')
                setSubcategoryFilter('')
                setTechniqueFilter('')
                setSourceFilter('')
              }}
              sx={{ minWidth: 100 }}
            >
              Clear Filters
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Prompts Table */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Prompts ({filteredPrompts.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openCreateModal}
            >
              Add Prompt
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : filteredPrompts.length === 0 ? (
            <Paper variant="outlined" sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
              <Typography variant="h6" gutterBottom>
                No prompts found
              </Typography>
              <Typography variant="body2">
                Adjust filters or add a prompt to get started.
              </Typography>
            </Paper>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ minWidth: 200, maxWidth: 300 }}>Prompt</TableCell>
                    <TableCell sx={{ minWidth: 180, maxWidth: 250 }}>ID</TableCell>
                    <TableCell>Attack Technique</TableCell>
                    <TableCell>Vulnerability Category</TableCell>
                    <TableCell>Vulnerability Subcategory</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell sx={{ width: 120 }}></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredPrompts.map((prompt, index) => (
                    <TableRow
                      key={prompt.id}
                      sx={{ 
                        cursor: 'pointer',
                        backgroundColor: hoveredRow === prompt.id ? '#f5f5f5' : (index % 2 === 0 ? 'white' : '#f8f9fa'),
                        '&:hover': {
                          backgroundColor: '#f5f5f5'
                        }
                      }}
                      onMouseEnter={() => setHoveredRow(prompt.id)}
                      onMouseLeave={() => setHoveredRow(null)}
                      onClick={() => viewPrompt(prompt)}
                    >
                      <TableCell sx={{ minWidth: 200, maxWidth: 300 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                          title={prompt.prompt}
                        >
                          {prompt.prompt}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ minWidth: 180, maxWidth: 250 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            fontWeight: 'medium',
                            color: 'text.secondary'
                          }}
                          title={prompt.id}
                        >
                          {prompt.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatText(prompt.attack_technique)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatText(prompt.vuln_category)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatText(prompt.vuln_subcategory)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {prompt.source === 'file' ? 'File' : 'Local'}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ width: 120 }}>
          <Box 
            display="flex" 
                          gap={1}
                          sx={{
                            opacity: hoveredRow === prompt.id ? 1 : 0,
                            transition: 'opacity 0.2s ease'
                          }}
                        >
                          <CustomTooltip title="View Details">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={(e) => {
                                e.stopPropagation()
                                viewPrompt(prompt)
                              }}
                            >
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </CustomTooltip>
                          
                          <CopyToClipboard
                            text={prompt.prompt}
                            onCopy={() => handleCopyPrompt(prompt.id)}
                          >
                            <CustomTooltip title={copiedPromptId === prompt.id ? "Copied!" : "Copy Prompt"}>
                              <IconButton
                                size="small"
                                color={copiedPromptId === prompt.id ? "success" : "default"}
                                onClick={(e) => e.stopPropagation()}
                              >
                                <CopyIcon fontSize="small" />
                              </IconButton>
                            </CustomTooltip>
                          </CopyToClipboard>


                          <CustomTooltip title="Delete Prompt">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => {
                                e.stopPropagation()
                                deletePrompt(prompt.id)
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </CustomTooltip>
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

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={openCreateModal}
      >
        <AddIcon />
      </Fab>

      {/* Prompt Details Overlay */}
      <SlideOverlay
        open={!!selectedPrompt}
        onClose={() => setSelectedPrompt(null)}
        title={selectedPrompt?.prompt.id}
        width={700}
        actions={
          selectedPrompt && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                size="small"
                onClick={() => {
                  openEditModal(selectedPrompt.prompt)
                  setSelectedPrompt(null)
                }}
              >
                Edit
              </Button>
            </Box>
          )
        }
      >
        {selectedPrompt && (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3, pt: 2 }}>
              <Tabs value={overlayTab} onChange={(_, newValue) => setOverlayTab(newValue)}>
                <Tab label="Details" icon={<SecurityIcon />} iconPosition="start" />
                <Tab label="Usage" icon={<ChatIcon />} iconPosition="start" />
              </Tabs>
            </Box>

            {/* Tab Content */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              {overlayTab === 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Prompt Details
                  </Typography>
                  
                  <Card variant="outlined" sx={{ mb: 3 }}>
                    <CardContent>
                      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Prompt ID
                          </Typography>
                          <Typography variant="body1" fontWeight="medium" sx={{ color: 'text.primary' }}>
                            {selectedPrompt.prompt.id}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Attack Technique
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {formatText(selectedPrompt.prompt.attack_technique)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Vulnerability Category
                          </Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {formatText(selectedPrompt.prompt.vuln_category)}
                          </Typography>
                        </Box>
                        {selectedPrompt.prompt.vuln_subcategory && (
                          <Box>
                            <Typography variant="caption" color="textSecondary">
                              Vulnerability Subcategory
                            </Typography>
                            <Typography variant="body1" fontWeight="medium">
                              {formatText(selectedPrompt.prompt.vuln_subcategory)}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>

                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="h6" color="textSecondary">
                        Prompt Text
                      </Typography>
                      <CopyToClipboard text={selectedPrompt.prompt.prompt}>
                        <IconButton
                          size="small"
                          sx={{ color: 'text.secondary' }}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </CopyToClipboard>
                    </Box>
                    <Paper variant="outlined" sx={{ p: 2, mt: 0.5, bgcolor: 'background.default' }}>
                      <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                        {selectedPrompt.prompt.prompt}
                      </Typography>
                    </Paper>
                  </Box>

                  {/* Mappings */}
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Framework Mappings
                    </Typography>
                    
                    <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
                      <CardContent>
                        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Typography variant="subtitle2">
                            MITRE ATLAS:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {selectedPrompt.prompt.mitreatlasmapping && selectedPrompt.prompt.mitreatlasmapping.length > 0 ? (
                              selectedPrompt.prompt.mitreatlasmapping.map((mapping, index) => (
                                <Chip
                                  key={index}
                                  label={mapping}
                                  size="small"
                                  variant="outlined"
                                  sx={{ 
                                    borderColor: 'text.primary',
                                    color: 'text.primary'
                                  }}
                                />
                              ))
                            ) : (
                              <Chip
                                label="NIL"
                                size="small"
                                variant="outlined"
                                sx={{ 
                                  borderColor: 'text.secondary',
                                  color: 'text.secondary'
                                }}
                              />
                            )}
                          </Box>
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Typography variant="subtitle2">
                            OWASP Top 10 LLM:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {selectedPrompt.prompt.owasp_top10_llm_mapping && selectedPrompt.prompt.owasp_top10_llm_mapping.length > 0 ? (
                              selectedPrompt.prompt.owasp_top10_llm_mapping.map((mapping: string, index: number) => (
                                <Chip
                                  key={index}
                                  label={mapping}
                                  size="small"
                                  variant="outlined"
                                  sx={{ 
                                    borderColor: 'text.primary',
                                    color: 'text.primary'
                                  }}
                                />
                              ))
                            ) : (
                              <Chip
                                label="NIL"
                                size="small"
                                variant="outlined"
                                sx={{ 
                                  borderColor: 'text.secondary',
                                  color: 'text.secondary'
                                }}
                              />
                            )}
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Box>

                  {/* Collections */}
                  {(() => {
                    const collectionIds = Array.isArray(selectedPrompt.prompt.collection_id)
                      ? selectedPrompt.prompt.collection_id
                      : selectedPrompt.prompt.collection_id
                      ? [selectedPrompt.prompt.collection_id]
                      : []
                    return collectionIds.length > 0 ? (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="h6" gutterBottom>
                          Collections part of
                        </Typography>
                        <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
                          <CardContent>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {collectionIds.map((cid: string, idx: number) => (
                                <Chip
                                  key={`${cid}-${idx}`}
                                  label={cid}
                                  size="small"
                                  variant="outlined"
                                  sx={{ borderColor: 'text.primary', color: 'text.primary' }}
                                />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </Box>
                    ) : null
                  })()}
                </Box>
              )}

              {overlayTab === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Usage Statistics
                  </Typography>
                  
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2, mb: 3 }}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="primary.main" fontWeight="bold">
                          {selectedPrompt.prompt.usage_count || 0}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Times Used
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main" fontWeight="bold">
                          {selectedPrompt.prompt.success_rate || 0}%
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Success Rate
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="info.main" fontWeight="bold">
                          {selectedPrompt.relatedSessions.length}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Sessions
                        </Typography>
        </CardContent>
      </Card>
                  </Box>

                  <Typography variant="h6" gutterBottom>
                    Related Sessions
                  </Typography>
                  
                  {selectedPrompt.relatedSessions.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <ChatIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="body1" color="textSecondary">
                        This prompt hasn't been used in any sessions yet.
                      </Typography>
                    </Box>
                  ) : (
                    <List>
                      {selectedPrompt.relatedSessions.map((session: any, index: number) => (
                        <ListItem
                          key={session.session_id || session.id || index}
                          button
                          onClick={() => {
                            // Navigate to sessions page with the session ID
                            navigate(`/sessions/${session.session_id || session.id}`)
                          }}
                          sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            mb: 1,
                            '&:hover': {
                              bgcolor: 'action.hover',
                              cursor: 'pointer'
                            }
                          }}
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="body2" fontWeight="medium">
                                    {session.session_name || session.name || 'Unnamed Session'}
                                  </Typography>
                                  <Typography variant="caption" color="textSecondary" fontFamily="monospace" sx={{ display: 'block', mt: 0.5 }}>
                                    {session.session_id || session.id || 'Unknown ID'}
                                  </Typography>
                                </Box>
                                <Chip
                                  label={session.prompt_status || session.status || 'Unknown'}
                                  size="small"
                                  color={
                                    (session.prompt_status || session.status) === 'passed'
                                      ? 'success'
                                      : (session.prompt_status || session.status) === 'failed'
                                      ? 'error'
                                      : 'default'
                                  }
                                />
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Box>
              )}

            </Box>
          </Box>
        )}
      </SlideOverlay>

      {/* Create/Edit Prompt Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingPrompt ? 'Edit Prompt' : 'Create New Prompt'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Prompt ID"
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value })}
              disabled={!!editingPrompt}
              fullWidth
            />
            <FormControl fullWidth required>
              <InputLabel required>Source</InputLabel>
              <Select
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value, target_file: '' })}
                label="Source"
                disabled={!!editingPrompt}
              >
                <MenuItem value="local">Local Database</MenuItem>
                <MenuItem value="file">YAML File</MenuItem>
              </Select>
            </FormControl>
            {!editingPrompt && (
              <>
                {formData.source === 'file' && (
                  <FormControl fullWidth>
                    <InputLabel>Target File</InputLabel>
                    <Select
                      value={newFileMode ? '__new_file__' : formData.target_file}
                      onChange={(e) => {
                        const value = e.target.value as string
                        if (value === '__new_file__') {
                          setNewFileMode(true)
                          setFormData({ ...formData, target_file: '' })
                        } else {
                          setNewFileMode(false)
                          setNewFileName('')
                          setFormData({ ...formData, target_file: value })
                        }
                      }}
                      label="Target File"
                    >
                      {availableFiles.map((file) => (
                        <MenuItem key={file} value={file}>
                          {file}
                        </MenuItem>
                      ))}
                      <Divider />
                      <MenuItem value="__new_file__">Add new file</MenuItem>
                    </Select>
                  </FormControl>
                )}
                {formData.source === 'file' && newFileMode && (
                  <TextField
                    label="File name"
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    fullWidth
                    helperText="We will append .yaml if you leave it off"
                  />
                )}
              </>
            )}
            <TextField
              label="Attack Technique"
              required
              value={formData.attack_technique}
              onChange={(e) => setFormData({ ...formData, attack_technique: e.target.value })}
              fullWidth
            />
            <TextField
              label="Vulnerability Category"
              required
              value={formData.vulnerability_category}
              onChange={(e) => setFormData({ ...formData, vulnerability_category: e.target.value })}
              fullWidth
            />
            <TextField
              label="Vulnerability Subcategory"
              value={formData.vulnerability_subcategory}
              onChange={(e) => setFormData({ ...formData, vulnerability_subcategory: e.target.value })}
              fullWidth
            />
            <FormControl fullWidth required>
              <InputLabel required>Severity</InputLabel>
              <Select
                value={formData.severity}
                label="Severity"
                onChange={(e) => setFormData({ ...formData, severity: e.target.value as string })}
              >
                <MenuItem value="Low">Low</MenuItem>
                <MenuItem value="Medium">Medium</MenuItem>
                <MenuItem value="High">High</MenuItem>
                <MenuItem value="Critical">Critical</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Prompt Text"
              required
              value={formData.prompt_text}
              onChange={(e) => setFormData({ ...formData, prompt_text: e.target.value })}
              multiline
              rows={4}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSavePrompt}
            disabled={
              !formData.prompt_text ||
              !formData.severity ||
              !formData.attack_technique ||
              !formData.vulnerability_category ||
              (!editingPrompt &&
                formData.source === 'file' &&
                ((!newFileMode && !formData.target_file) || (newFileMode && !newFileName.trim())))
            }
          >
            {editingPrompt ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast notification for copy action */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbarOpen(false)} severity="success" sx={{ width: '100%' }}>
          Prompt copied to clipboard!
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default Prompts
