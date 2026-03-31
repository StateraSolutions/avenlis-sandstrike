import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
  CircularProgress,
  Chip,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  InputAdornment,
  Grid
} from '@mui/material'
import {
  PlayArrow as RunIcon,
  Close as CloseIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Science as TestIcon,
  Visibility as ViewResultsIcon
} from '@mui/icons-material'
import axios from 'axios'
import { useSocket } from '../contexts/SocketContext'
import { useSubscription } from '../contexts/SubscriptionContext'
import CustomDropdown, { DropdownOption } from '../components/common/CustomDropdown'

interface Collection {
  id: string
  name: string
  description: string
  prompt_ids: string[]
  prompt_count?: number
  type?: 'local' | 'yaml'
}

interface Prompt {
  id: string
  attack_technique: string
  vuln_category: string
  vuln_subcategory: string | null
  prompt: string
}


interface ScanResult {
  sessionId: string
  status: string
  progress: number
  logs: string[]
  results?: any
}

const Scan: React.FC = () => {
  const [scanName, setScanName] = useState('')
  const [scanId, setScanId] = useState('')
  const [target, setTarget] = useState('http://localhost:11434')
  const [model, setModel] = useState('')
  const [collections, setCollections] = useState<Collection[]>([])
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [targets, setTargets] = useState<any[]>([])
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null)
  const [selectedCollection, setSelectedCollection] = useState<string[]>([])
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>([])
  const [grader, setGrader] = useState('ollama')
  const [graderIntent, setGraderIntent] = useState('safety_evaluation')
  const [scanMode, setScanMode] = useState<'rapid' | 'full' | ''>('')
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [promptSelectorOpen, setPromptSelectorOpen] = useState(false)
  const [datasetSelectorOpen, setDatasetSelectorOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredPrompts, setFilteredPrompts] = useState<Prompt[]>([])
  const [anthropicKeySet, setAnthropicKeySet] = useState(false)
  const [geminiKeySet, setGeminiKeySet] = useState(false)
  const [testConnectionMessage, setTestConnectionMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null)
  const [gradingIntents, setGradingIntents] = useState<Record<string, { name: string, description: string }>>({})
  const [datasetPrompts, setDatasetPrompts] = useState<Record<string, Prompt[]>>({})
  const [loadingDataset, setLoadingDataset] = useState(false)
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>([])
  const [datasetSampleSizes, setDatasetSampleSizes] = useState<Record<string, number>>({
    'nvidia/Aegis-AI-Content-Safety-Dataset-1.0': 100,
    'PKU-Alignment/BeaverTails': 100
  })
  const [selectedDatasetPrompts, setSelectedDatasetPrompts] = useState<Record<string, Prompt[]>>({})
  const [datasetsToLoad, setDatasetsToLoad] = useState<string[]>([])
  const { socket } = useSocket()
  const { isProUser, isReady: isSubscriptionReady } = useSubscription()
  const navigate = useNavigate()

  // Calculate individual prompts count (excluding prompts from selected collections)
  const individualPromptsCount = selectedPrompts.filter(promptId => {
    // Check if this prompt is already included in any selected collection
    const isInCollection = selectedCollection.some(collectionId => {
      const collection = collections.find(c => c.id === collectionId)
      return collection && collection.prompt_ids && collection.prompt_ids.includes(promptId)
    })
    return !isInCollection
  }).length

  // Helper function to count valid (non-blank) prompt IDs
  const getValidPromptCount = (collection: Collection): number => {
    if (collection.prompt_count !== undefined) {
      return collection.prompt_count
    }
    if (collection.prompt_ids && Array.isArray(collection.prompt_ids)) {
      // Filter out blank/empty/null prompt IDs
      const validIds = collection.prompt_ids.filter(pid => pid && String(pid).trim())
      return validIds.length
    }
    return 0
  }

  // Get collection options for CustomDropdown
  const getCollectionOptions = (): DropdownOption[] => {
    const options: DropdownOption[] = []
    
    // Add local collections
    const localCollections = collections.filter(c => c.type === 'local' || !c.type)
    if (localCollections.length > 0) {
      localCollections.forEach(collection => {
        const promptCount = getValidPromptCount(collection)
        const isDisabled = promptCount === 0
        options.push({
          value: collection.id,
          label: `${collection.name} (${promptCount})`,
          disabled: isDisabled
        })
      })
    }
    
    // Add file collections
    const fileCollections = collections.filter(c => c.type === 'yaml')
    if (fileCollections.length > 0) {
      fileCollections.forEach(collection => {
        const promptCount = getValidPromptCount(collection)
        const isDisabled = promptCount === 0
        options.push({
          value: collection.id,
          label: `${collection.name} (${promptCount})`,
          disabled: isDisabled
        })
      })
    }
    
    return options
  }

  useEffect(() => {
    loadInitialData()
    loadLLMConfigStatus()
    checkRunningScans()
  }, [])

  const checkRunningScans = async () => {
    try {
      // Check if there are any running sessions
      const response = await axios.get('/api/sessions?status=running')
      const runningSessions = response.data.sessions || response.data || []
      if (runningSessions.length > 0) {
        setScanning(true)
        setScanResult({
          sessionId: runningSessions[0].id || '',
          status: 'running',
          progress: 0,
          logs: []
        })
      }
    } catch (error) {
      console.error('Failed to check running scans:', error)
    }
  }

  useEffect(() => {
    if (socket) {
      socket.on('scan_complete', handleScanComplete)
      socket.on('scan_error', handleScanError)
      return () => {
        socket.off('scan_complete', handleScanComplete)
        socket.off('scan_error', handleScanError)
      }
    }
  }, [socket])

  useEffect(() => {
    filterPrompts()
  }, [prompts, searchTerm])

  useEffect(() => {
    // Load prompts from selected collections
    if (selectedCollection.length > 0) {
      const selectedCollections = collections.filter(c => selectedCollection.includes(c.id))
      // Filter out blank/empty/null prompt IDs before flattening
      const allPromptIds = selectedCollections.flatMap(c => {
        const ids = c.prompt_ids || []
        return ids.filter(pid => pid && String(pid).trim())
      })
      
      // Filter prompts based on the prompt IDs from selected collections
      const filteredPrompts = prompts.filter(p => allPromptIds.includes(p.id))
      
      // Get current individual prompts (prompts not in any collection)
      const currentIndividualPrompts = selectedPrompts.filter(promptId => {
        const isInAnyCollection = collections.some(collection => 
          collection.prompt_ids && collection.prompt_ids.includes(promptId)
        )
        return !isInAnyCollection
      })
      
      // Combine collection prompts with individual prompts
      const combinedPrompts = [...filteredPrompts.map(p => p.id), ...currentIndividualPrompts]
      setSelectedPrompts(combinedPrompts)
      
    } else {
      // When no collections are selected, keep only individual prompts
      const individualPrompts = selectedPrompts.filter(promptId => {
        const isInAnyCollection = collections.some(collection => 
          collection.prompt_ids && collection.prompt_ids.includes(promptId)
        )
        return !isInAnyCollection
      })
      setSelectedPrompts(individualPrompts)
    }
  }, [selectedCollection, collections, prompts])

  const loadInitialData = async () => {
    try {
      const [collectionsRes, promptsRes, intentsRes, targetsRes] = await Promise.all([
        axios.get('/api/collections'),
        axios.get('/api/prompts'),
        axios.get('/api/grading-intents'),
        axios.get('/api/targets')
      ])
      setCollections(collectionsRes.data.collections || [])
      setPrompts(promptsRes.data.prompts || [])
      setGradingIntents(intentsRes.data.grading_intents || {})
      setTargets(targetsRes.data.targets || [])
    } catch (error) {
      console.error('Failed to load initial data:', error)
    }
  }

  const loadLLMConfigStatus = async () => {
    try {
      const response = await axios.get('/api/config/llm-status')
      setAnthropicKeySet(response.data.anthropic_key_set)
      setGeminiKeySet(response.data.gemini_key_set)
    } catch (error) {
      console.error('Failed to load LLM config status:', error)
    }
  }

  const filterPrompts = () => {
    const filtered = prompts.filter(prompt =>
      prompt.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.attack_technique.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.prompt.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredPrompts(filtered)
  }

  const handleScanComplete = (data: any) => {
    setScanning(false)
    setScanResult(prev => ({
      ...prev!,
      status: 'completed',
      results: data.results
    }))
  }

  const handleScanError = (data: any) => {
    setScanning(false)
    setScanResult(prev => ({
      ...prev!,
      status: 'error',
      logs: [...(prev?.logs || []), `Error: ${data.error}`]
    }))
  }

  const testConnection = async () => {
    // Check if this is an Ollama target
    const selectedTargetData = selectedTarget && selectedTarget !== 'custom' 
      ? targets.find(t => t.id === selectedTarget) 
      : null
    const isOllamaTarget = selectedTargetData?.target_type === 'Ollama' || 
                          (selectedTarget === 'custom' && target && target.includes('localhost:11434'))
    
    // Use model from target if available, otherwise use the model state (for custom targets)
    const modelToUse = selectedTargetData?.model || model
    
    if (!target) {
      setTestConnectionMessage({ type: 'error', text: 'Please specify target URL' })
      return
    }
    
    if (isOllamaTarget && !modelToUse) {
      setTestConnectionMessage({ type: 'error', text: 'Please specify model name for Ollama targets' })
      return
    }

    setLoading(true)
    setTestConnectionMessage(null)
    try {
      // Only test Ollama connection if it's an Ollama target
      if (isOllamaTarget) {
        const response = await axios.post('/api/test-ollama', {
          url: target,
          model: modelToUse
        })
        setTestConnectionMessage({ type: 'success', text: response.data.message })
      } else {
        // For URL targets, just validate the URL format
        try {
          new URL(target)
          setTestConnectionMessage({ type: 'success', text: 'URL format is valid' })
        } catch {
          setTestConnectionMessage({ type: 'error', text: 'Invalid URL format' })
        }
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.response?.data?.message || error.message || 'Connection test failed'
      setTestConnectionMessage({ type: 'error', text: errorMessage })
    } finally {
      setLoading(false)
    }
  }

  const runScan = async () => {
    // Prevent starting a new scan if one is already running
    if (scanning) {
      alert('A scan is currently running. Please wait for it to complete before starting a new one.')
      return
    }

    // Disable button immediately to prevent multiple clicks
    setScanning(true)

    if (!target) {
      setScanning(false)
      alert('Please specify target URL')
      return
    }
    
    // Check if this is an Ollama target
    const selectedTargetData = selectedTarget && selectedTarget !== 'custom' 
      ? targets.find(t => t.id === selectedTarget) 
      : null
    const isOllamaTarget = selectedTargetData?.target_type === 'Ollama' || 
                          (selectedTarget === 'custom' && target && target.includes('localhost:11434'))
    
    // Use model from target if available, otherwise use the model state (for custom targets)
    const modelToUse = selectedTargetData?.model || model
    
    if (isOllamaTarget && !modelToUse) {
      setScanning(false)
      alert('Please specify model name for Ollama targets')
      return
    }

    const totalDatasetPrompts = Object.values(selectedDatasetPrompts).flat().length
    if (selectedCollection.length === 0 && selectedPrompts.length === 0 && totalDatasetPrompts === 0) {
      setScanning(false)
      alert('Please select at least one of: collections, individual prompts, or datasets to run the scan')
      return
    }

    if (!grader) {
      setScanning(false)
      alert('Please select a response grader to continue')
      return
    }

    if (!scanMode) {
      setScanning(false)
      alert('Please select a scan mode (Rapid Scan or Full Scan)')
      return
    }

    // Validate Pro subscription for Avenlis Copilot Grader
    if (grader === 'avenlis_copilot' && !isProUser) {
      setScanning(false)
      alert('Avenlis Copilot Grader requires a Pro subscription. Please upgrade your account.')
      return
    }

    // Test connection before starting scan (only for Ollama targets)
    if (isOllamaTarget) {
      setLoading(true)
      setTestConnectionMessage({ type: 'info', text: 'Testing connection to target...' })
      
      try {
        const connectionResponse = await axios.post('/api/test-ollama', {
          url: target,
          model: modelToUse
        })
        setTestConnectionMessage({ type: 'success', text: connectionResponse.data.message })
      } catch (error: any) {
        setLoading(false)
        setScanning(false)
        const errorMessage = error.response?.data?.message || 'Connection test failed'
        setTestConnectionMessage({ type: 'error', text: errorMessage })
        alert(`Connection test failed: ${errorMessage}\n\nPlease check your target URL and model, then try again.`)
        return
      } finally {
        setLoading(false)
      }
    }

    setScanResult({
      sessionId: '',
      status: 'running',
      progress: 0,
      logs: []
    })

    try {
      const timestamp = Date.now()
      const defaultScanName = `Test ${new Date(timestamp).toLocaleString()}`
      const defaultScanId = `scan_${timestamp}`
      const finalScanName = scanName.trim() || defaultScanName
      const finalScanId = scanId.trim() || defaultScanId

      // Combine selected prompts with dataset prompts from all selected datasets
      const allDatasetPromptIds = Object.values(selectedDatasetPrompts).flat().map(p => p.id)
      const allPromptIds = [
        ...selectedPrompts,
        ...allDatasetPromptIds
      ]
      
      const scanConfig = {
        target,
        model: modelToUse,
        scan_type: scanMode as 'rapid' | 'full',
        storage_type: scanMode === 'rapid' ? 'local' : 'yaml',
        scan_name: finalScanName,
        scan_id: finalScanId,
        grader_config: {
          enabled: true,
          grader: grader,
          grader_intent: graderIntent
        },
        ...(selectedCollection.length > 0 && { collection_ids: selectedCollection }),
        ...(allPromptIds.length > 0 && { prompt_ids: allPromptIds })
      }

      const response = await axios.post('/api/redteam/run', scanConfig)
      
      if (response.data.error) {
        throw new Error(response.data.error)
      }

      setScanResult(prev => ({
        ...prev!,
        sessionId: response.data.session_id,
        logs: []
      }))

    } catch (error: any) {
      setScanning(false)
      setScanResult(prev => ({
        ...prev!,
        status: 'error',
        logs: [...(prev?.logs || []), `[FAILED] Scan failed: ${error.response?.data?.error || error.message}`]
      }))
    }
  }

  const handlePromptToggle = (promptId: string) => {
    setSelectedPrompts(prev =>
      prev.includes(promptId)
        ? prev.filter(id => id !== promptId)
        : [...prev, promptId]
    )
  }

  const openPromptSelector = () => {
    setPromptSelectorOpen(true)
  }

  const closePromptSelector = () => {
    setPromptSelectorOpen(false)
  }

  const openDatasetSelector = () => {
    // Initialize with currently selected datasets
    setDatasetsToLoad([...selectedDatasets])
    setDatasetSelectorOpen(true)
  }

  const closeDatasetSelector = () => {
    setDatasetSelectorOpen(false)
    // Reset to currently selected datasets if cancelled
    setDatasetsToLoad([...selectedDatasets])
  }

  const loadSelectedDatasets = async () => {
    if (datasetsToLoad.length === 0) {
      closeDatasetSelector()
      return
    }

    try {
      setLoadingDataset(true)
      
      // Load all selected datasets
      for (const datasetName of datasetsToLoad) {
        const response = await axios.post('/api/datasets/huggingface/load', {
          dataset_name: datasetName
        })
        
        if (response.data.success && response.data.prompts) {
          const allPrompts = response.data.prompts
          const sampleSize = datasetSampleSizes[datasetName] || 100
          
          // Randomly sample prompts
          const shuffled = [...allPrompts].sort(() => 0.5 - Math.random())
          const sampled = shuffled.slice(0, Math.min(sampleSize, allPrompts.length))
          
          // Save sampled prompts to local storage
          const savePromises = sampled.map(async (prompt: any) => {
            try {
              await axios.post('/api/prompts', {
                prompt_id: prompt.id,
                prompt_text: prompt.prompt,
                attack_technique: prompt.attack_technique,
                vuln_category: prompt.vuln_category,
                vuln_subcategory: prompt.vuln_subcategory,
                severity: prompt.severity,
                owasp_top10_llm_mapping: prompt.owasp_top10_llm_mapping || [],
                mitreatlasmapping: prompt.mitreatlasmapping || [],
                source: 'local'
              })
            } catch (err) {
              console.error(`Failed to save prompt ${prompt.id}:`, err)
            }
          })
          
          await Promise.all(savePromises)
          
          // Store dataset data
          setDatasetPrompts(prev => ({
            ...prev,
            [datasetName]: allPrompts
          }))
          setSelectedDatasetPrompts(prev => ({
            ...prev,
            [datasetName]: sampled
          }))
        }
      }
      
      // Reload prompts to get the updated list
      await loadInitialData()
      
      // Update selected datasets
      setSelectedDatasets(datasetsToLoad)
      setDatasetsToLoad([])
      closeDatasetSelector()
    } catch (error: any) {
      console.error('Failed to load datasets:', error)
      
      let errorMessage = 'Failed to load dataset. '
      if (error.response?.data?.error) {
        errorMessage += error.response.data.error
        if (error.response.data.details) {
          errorMessage += '\n\n' + error.response.data.details
        }
      } else {
        errorMessage += 'Please check the console for details.'
      }
      
      alert(errorMessage)
    } finally {
      setLoadingDataset(false)
    }
  }

  const removeDataset = (datasetName: string) => {
    setDatasetPrompts(prev => {
      const newPrompts = { ...prev }
      delete newPrompts[datasetName]
      return newPrompts
    })
    setSelectedDatasets(prev => prev.filter(d => d !== datasetName))
    setSelectedDatasetPrompts(prev => {
      const newPrompts = { ...prev }
      const oldPromptIds = (newPrompts[datasetName] || []).map(p => p.id)
      delete newPrompts[datasetName]
      // Remove old prompts from selection
      setSelectedPrompts(prevSelected => prevSelected.filter(id => !oldPromptIds.includes(id)))
      return newPrompts
    })
  }

  const resampleDataset = async (datasetName: string, newSampleSize: number) => {
    const allPrompts = datasetPrompts[datasetName]
    if (!allPrompts || allPrompts.length === 0) return
    
    // Re-sample from the already loaded dataset
    const shuffled = [...allPrompts].sort(() => 0.5 - Math.random())
    const sampled = shuffled.slice(0, Math.min(newSampleSize, allPrompts.length))
    
    // Remove old prompts from selection
    const oldPromptIds = (selectedDatasetPrompts[datasetName] || []).map(p => p.id)
    setSelectedPrompts(prev => prev.filter(id => !oldPromptIds.includes(id)))
    
    // Save new sampled prompts to local storage
    const savePromises = sampled.map(async (prompt: any) => {
      try {
        await axios.post('/api/prompts', {
          prompt_id: prompt.id,
          prompt_text: prompt.prompt,
          attack_technique: prompt.attack_technique,
          vuln_category: prompt.vuln_category,
          vuln_subcategory: prompt.vuln_subcategory,
          severity: prompt.severity,
          owasp_top10_llm_mapping: prompt.owasp_top10_llm_mapping || [],
          mitreatlasmapping: prompt.mitreatlasmapping || [],
          source: 'local'
        })
      } catch (err) {
        // Prompt might already exist, which is fine
      }
    })
    
    await Promise.all(savePromises)
    
    // Add new sampled prompts to selection
    const newPromptIds = sampled.map(p => p.id)
    setSelectedPrompts(prev => [...prev, ...newPromptIds])
    
    setSelectedDatasetPrompts(prev => ({
      ...prev,
      [datasetName]: sampled
    }))
    
    // Reload prompts to get the updated list
    await loadInitialData()
  }

  // Get button text and styling based on scan status
  const getButtonState = () => {
    if (scanning) {
      return {
        text: 'Running Test...',
        disabled: true,
        icon: undefined,
        color: 'rgba(255,255,255,0.1)',
        textColor: 'rgba(255,255,255,0.5)',
        onClick: undefined
      }
    }
    
    if (scanResult?.status === 'error') {
      return {
        text: 'Scan Failed - Click to Retry',
        disabled: false,
        icon: <RunIcon />,
        color: 'rgba(244, 67, 54, 0.8)', // Red background
        textColor: 'white',
        onClick: runScan
      }
    }
    
    if (scanResult?.status === 'completed') {
      return {
        text: 'View Results',
        disabled: false,
        icon: <ViewResultsIcon />,
        color: 'rgba(76, 175, 80, 0.8)', // Green background
        textColor: 'white',
        onClick: () => navigate('/sessions')
      }
    }
    
    // Default state
    return {
      text: 'Start Scan',
      disabled: false,
      icon: <RunIcon />,
      color: 'rgba(255,255,255,0.2)',
      textColor: 'white',
      onClick: runScan
    }
  }

  const buttonState = getButtonState()

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', overflow: 'visible' }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Run Scan
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Test your LLMs and AI models against adversarial prompts
        </Typography>
      </Box>

      {/* Main Configuration Grid */}
      <Grid container spacing={4}>
        {/* Left Column - Configuration */}
        <Grid item xs={12} lg={8}>
          {/* Scan Configuration */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 2 }}>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" fontWeight="bold">
                  Scan Configuration
                </Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scan ID"
                    value={scanId}
                    onChange={(e) => setScanId(e.target.value)}
                    placeholder="Leave blank for auto-generated ID"
                    helperText="Optional: Custom ID for this scan session"
                    variant="outlined"
                    sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scan Name"
                    value={scanName}
                    onChange={(e) => setScanName(e.target.value)}
                    placeholder="Enter a name for your scan"
                    helperText="Optional: Give your scan a descriptive name"
                    variant="outlined"
                    sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                  />
                </Grid>
                {targets.length > 0 && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                      <FormControl fullWidth>
                        <InputLabel>Select Target</InputLabel>
                        <Select
                          value={selectedTarget || ''}
                          onChange={(e) => {
                            const targetId = e.target.value
                            setSelectedTarget(targetId || null)
                            const selected = targets.find(t => t.id === targetId)
                            if (selected) {
                              setTarget(selected.ip_address)
                              // Set model from target if it's an Ollama target
                              if (selected.target_type === 'Ollama' && selected.model) {
                                setModel(selected.model)
                              } else {
                                setModel('')
                              }
                            } else if (targetId === 'custom') {
                              // Clear fields when selecting "Custom Target"
                              setTarget('')
                              setModel('')
                            }
                          }}
                          displayEmpty
                          label="Select Target"
                          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                          renderValue={(selected) => {
                            if (!selected || selected === '') {
                              return 'Select a target'
                            }
                            if (selected === 'custom') {
                              return 'Custom Target'
                            }
                            const target = targets.find(t => t.id === selected)
                            return target ? `${target.name} - ${target.ip_address}` : ''
                          }}
                        >
                          {targets.map((t) => (
                            <MenuItem key={t.id} value={t.id}>
                              {t.name} - {t.ip_address}
                            </MenuItem>
                          ))}
                          <Divider />
                          <MenuItem value="custom">
                            Custom Target
                          </MenuItem>
                        </Select>
                      </FormControl>
                      <Button
                        variant="outlined"
                        onClick={testConnection}
                        disabled={
                          loading || 
                          !selectedTarget || 
                          selectedTarget === '' ||
                          (selectedTarget === 'custom' && (!target || !model))
                        }
                        startIcon={loading ? <CircularProgress size={20} /> : <TestIcon />}
                        sx={{ 
                          px: 3, 
                          py: 1.75, 
                          borderRadius: 2,
                          borderWidth: 2,
                          minWidth: 'fit-content',
                          whiteSpace: 'nowrap',
                          '&:hover': { borderWidth: 2 }
                        }}
                      >
                        Test Connection
                      </Button>
                    </Box>
                  </Grid>
                )}
                {(targets.length === 0 || selectedTarget === 'custom') && (
                  <>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Target URL"
                        value={target}
                        onChange={(e) => {
                          setTarget(e.target.value)
                          if (targets.length > 0) {
                            setSelectedTarget('custom') // Set to custom when manually editing
                          }
                        }}
                        placeholder="http://localhost:11434 or https://api.anthropic.com"
                        helperText="URL of your LLM server or API endpoint"
                        variant="outlined"
                        sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                        <TextField
                          fullWidth
                          label="Model Name"
                          value={model}
                          onChange={(e) => setModel(e.target.value)}
                          placeholder="e.g., llama2, mistral, codellama"
                          helperText="Name of the model to test (required for Ollama targets)"
                          variant="outlined"
                          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                        />
                        {targets.length === 0 && (
                          <Button
                            variant="outlined"
                            onClick={testConnection}
                            disabled={loading || !target || !model}
                            startIcon={loading ? <CircularProgress size={20} /> : <TestIcon />}
                            sx={{ 
                              px: 3, 
                              py: 1.75, 
                              borderRadius: 2,
                              borderWidth: 2,
                              minWidth: 'fit-content',
                              whiteSpace: 'nowrap',
                              mt: 0.5,
                              '&:hover': { borderWidth: 2 }
                            }}
                          >
                            Test Connection
                          </Button>
                        )}
                      </Box>
                    </Grid>
                  </>
                )}
              </Grid>

              {/* Test Connection Message */}
              {testConnectionMessage && (
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                  <Alert 
                    severity={testConnectionMessage.type} 
                    sx={{ 
                      borderRadius: 2,
                      maxWidth: '100%',
                      width: 'fit-content'
                    }}
                  >
                    {testConnectionMessage.text}
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Prompt Selection */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 2, overflow: 'visible' }}>
            <CardContent sx={{ p: 4, overflow: 'visible', pb: 6 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" fontWeight="bold">
                  Prompt Selection
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ 
                  bgcolor: 'grey.100', 
                  px: 2, 
                  py: 1, 
                  borderRadius: 1,
                  fontWeight: 'medium'
                }}>
                  Total Prompts: {selectedPrompts.length + Object.values(selectedDatasetPrompts).flat().length}
                </Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <CustomDropdown
                    label="Collections"
                    options={getCollectionOptions()}
                    selectedValues={selectedCollection}
                    onChange={setSelectedCollection}
                    placeholder="Select collections..."
                    maxWidth={400}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box>
                    <Typography variant="caption" color="textSecondary" sx={{ mb: 0.5, display: 'block' }}>
                      Individual Prompts
                    </Typography>
                    <Button
                      variant="outlined"
                      onClick={openPromptSelector}
                      startIcon={<AddIcon />}
                      fullWidth
                      sx={{ 
                        py: 2, 
                        borderRadius: 2,
                        borderWidth: 2,
                        '&:hover': { borderWidth: 2 }
                      }}
                    >
                      Add Individual Prompts
                      {individualPromptsCount > 0 && (
                        <Chip
                          label={individualPromptsCount}
                          size="small"
                          sx={{ ml: 2 }}
                        />
                      )}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Dataset Selection */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 2 }}>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" fontWeight="bold">
                  Dataset Selection
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ 
                  bgcolor: 'grey.100', 
                  px: 2, 
                  py: 1, 
                  borderRadius: 1,
                  fontWeight: 'medium'
                }}>
                  Dataset Prompts: {Object.values(selectedDatasetPrompts).flat().length}
                </Typography>
              </Box>

              {selectedDatasets.length > 0 ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {selectedDatasets.map((datasetName) => {
                    const datasetPromptsForThis = datasetPrompts[datasetName] || []
                    const selectedPromptsForThis = selectedDatasetPrompts[datasetName] || []
                    const getDatasetDisplayName = (name: string) => {
                      if (name === 'nvidia/Aegis-AI-Content-Safety-Dataset-1.0') return 'Aegis AI Content Safety Dataset'
                      if (name === 'PKU-Alignment/BeaverTails') return 'BeaverTails Dataset'
                      return 'Dataset'
                    }
                    
                    return (
                      <Card key={datasetName} variant="outlined" sx={{ p: 3, borderRadius: 2, backgroundColor: 'success.50' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" fontWeight="bold" gutterBottom>
                              {getDatasetDisplayName(datasetName)}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                              {datasetName}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              <Chip 
                                label={`${selectedPromptsForThis.length} prompts selected`}
                                color="success"
                                size="small"
                              />
                              <Chip 
                                label={`Total: ${datasetPromptsForThis.length} available`}
                                variant="outlined"
                                size="small"
                              />
                            </Box>
                          </Box>
                          <Button
                            variant="outlined"
                            color="error"
                            onClick={() => removeDataset(datasetName)}
                            sx={{ borderRadius: 2, ml: 2 }}
                          >
                            Remove
                          </Button>
                        </Box>
                        
                        <Divider sx={{ my: 2 }} />
                        
                        <Box>
                          <Typography variant="body2" fontWeight="medium" gutterBottom>
                            Sample Size
                          </Typography>
                          <TextField
                            fullWidth
                            type="number"
                            value={datasetSampleSizes[datasetName] || 100}
                            onChange={async (e) => {
                              const value = parseInt(e.target.value) || 1
                              const clampedValue = Math.max(1, Math.min(10000, value))
                              setDatasetSampleSizes(prev => ({
                                ...prev,
                                [datasetName]: clampedValue
                              }))
                              // Re-sample when sample size changes
                              if (datasetPromptsForThis.length > 0) {
                                await resampleDataset(datasetName, clampedValue)
                              }
                            }}
                            placeholder="100"
                            helperText="Number of random prompts to use from this dataset (1-10,000)"
                            variant="outlined"
                            size="small"
                            InputProps={{
                              inputProps: { 
                                min: 1, 
                                max: 10000 
                              }
                            }}
                            sx={{ 
                              '& .MuiOutlinedInput-root': { borderRadius: 2 }
                            }}
                          />
                        </Box>
                      </Card>
                    )
                  })}
                </Box>
              ) : (
                <Button
                  variant="outlined"
                  onClick={openDatasetSelector}
                  startIcon={<AddIcon />}
                  fullWidth
                  sx={{ 
                    py: 2.5, 
                    borderRadius: 2,
                    borderWidth: 2,
                    '&:hover': { borderWidth: 2 }
                  }}
                >
                  Add Dataset
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Grader Configuration */}
          <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 2 }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>
                Response Grader
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Grader</InputLabel>
                    <Select
                      value={grader}
                      onChange={(e) => setGrader(e.target.value)}
                      label="Grader"
                      sx={{ borderRadius: 2 }}
                    >
                      <MenuItem value="ollama">Ollama Grader (Local)</MenuItem>
                      <MenuItem 
                        value="anthropic" 
                        disabled={!anthropicKeySet}
                        sx={{ 
                          color: !anthropicKeySet ? '#9e9e9e' : 'inherit',
                          opacity: !anthropicKeySet ? 0.6 : 1
                        }}
                      >
                        Anthropic Grader{!anthropicKeySet ? ' (API Key Required)' : ''}
                        {!anthropicKeySet && (
                          <Chip 
                            label="No API Key" 
                            size="small" 
                            color="error" 
                            sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                          />
                        )}
                      </MenuItem>
                      <MenuItem 
                        value="gemini" 
                        disabled={!geminiKeySet}
                        sx={{ 
                          color: !geminiKeySet ? '#9e9e9e' : 'inherit',
                          opacity: !geminiKeySet ? 0.6 : 1
                        }}
                      >
                        Gemini Grader{!geminiKeySet ? ' (API Key Required)' : ''}
                        {!geminiKeySet && (
                          <Chip 
                            label="No API Key" 
                            size="small" 
                            color="error" 
                            sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                          />
                        )}
                      </MenuItem>
                      <MenuItem 
                        value="avenlis_copilot"
                        disabled={isSubscriptionReady && !isProUser}
                        sx={{ 
                          color: isSubscriptionReady && !isProUser ? '#9e9e9e' : 'inherit',
                          opacity: isSubscriptionReady && !isProUser ? 0.6 : 1
                        }}
                      >
                        Avenlis Copilot Grader
                        {isSubscriptionReady && !isProUser && (
                          <Chip 
                            label="Pro Only" 
                            size="small" 
                            color="warning" 
                            sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                          />
                        )}
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Grading Intent</InputLabel>
                    <Select
                      value={graderIntent}
                      onChange={(e) => setGraderIntent(e.target.value)}
                      label="Grading Intent"
                      sx={{ borderRadius: 2 }}
                    >
                      {Object.entries(gradingIntents).map(([key, intent]) => (
                        <MenuItem key={key} value={key}>
                          {intent.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Box sx={{ mt: 3 }}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend" sx={{ mb: 2, fontSize: '1.1rem', fontWeight: 600 }}>
                    Scan Mode
                  </FormLabel>
                  <RadioGroup
                    value={scanMode}
                    onChange={(e) => setScanMode(e.target.value as 'rapid' | 'full')}
                    sx={{ display: 'flex', flexDirection: 'row', gap: 2, width: '100%' }}
                  >
                    <FormControlLabel
                      value="full"
                      control={<Radio />}
                      label={
                        <Box sx={{ ml: 1 }}>
                          <Typography variant="body1" fontWeight="600" sx={{ mb: 0.5 }}>
                            Full Scan
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Store session data in file
                          </Typography>
                        </Box>
                      }
                      sx={{ 
                        border: '2px solid', 
                        borderColor: scanMode === 'full' ? 'primary.main' : 'grey.300',
                        borderRadius: 2,
                        p: 2,
                        m: 0,
                        flex: 1,
                        '&:hover': { borderColor: 'primary.main' }
                      }}
                    />
                    <FormControlLabel
                      value="rapid"
                      control={<Radio />}
                      label={
                        <Box sx={{ ml: 1 }}>
                          <Typography variant="body1" fontWeight="600" sx={{ mb: 0.5 }}>
                            Rapid Scan
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Store session data locally
                          </Typography>
                        </Box>
                      }
                      sx={{ 
                        border: '2px solid', 
                        borderColor: scanMode === 'rapid' ? 'primary.main' : 'grey.300',
                        borderRadius: 2,
                        p: 2,
                        m: 0,
                        flex: 1,
                        '&:hover': { borderColor: 'primary.main' }
                      }}
                    />
                  </RadioGroup>
                </FormControl>
              </Box>

              {grader === 'avenlis_copilot' && !isProUser && (
                <Alert severity="warning" sx={{ mt: 3 }}>
                  <Typography variant="body2">
                    Avenlis Copilot Grader requires a Pro subscription. 
                    <Button 
                      size="small" 
                      color="primary" 
                      sx={{ ml: 1 }}
                      onClick={() => window.open('https://avenlis.staterasolv.com/payment', '_blank')}
                    >
                      Upgrade Now
                    </Button>
                  </Typography>
                </Alert>
              )}

            </CardContent>
          </Card>

        </Grid>

        {/* Right Column - Action Button */}
        <Grid item xs={12} lg={4}>
          <Box sx={{ position: 'sticky', top: 24 }}>
            <Card sx={{ borderRadius: 2, boxShadow: 3, background: 'linear-gradient(135deg, #18727a 0%, #0d4d54 100%)' }}>
              <CardContent sx={{ p: 4, textAlign: 'center', color: 'white' }}>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Ready to Scan?
                </Typography>
                <Typography variant="body2" sx={{ mb: 3, opacity: 0.9 }}>
                  Configure your settings and run a comprehensive security test
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  onClick={buttonState.onClick}
                  disabled={buttonState.disabled}
                  startIcon={scanning ? undefined : buttonState.icon}
                  fullWidth
                  sx={{ 
                    py: 2.5, 
                    borderRadius: 2,
                    backgroundColor: buttonState.color,
                    color: buttonState.textColor,
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.3)',
                    '&:hover': {
                      backgroundColor: scanResult?.status === 'error' ? 'rgba(244, 67, 54, 0.9)' :
                                     scanResult?.status === 'completed' ? 'rgba(76, 175, 80, 0.9)' :
                                     'rgba(255,255,255,0.3)',
                    },
                    '&:disabled': {
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      color: 'rgba(255,255,255,0.5)'
                    }
                  }}
                >
                  {buttonState.text}
                </Button>
              </CardContent>
            </Card>
            
            {/* Alert when scan is running - below Ready to Scan card */}
            {scanning && (
              <Alert 
                severity="info" 
                sx={{ mt: 3, borderRadius: 2 }}
                icon={<CircularProgress size={20} />}
              >
                <Typography variant="body1" fontWeight="medium">
                  A test is currently running
                </Typography>
                <Typography variant="body2">
                  Please wait for the current scan to complete before starting a new one.
                </Typography>
              </Alert>
            )}
          </Box>
        </Grid>
      </Grid>

      {/* Scan Results - Only show error or completion messages */}
      {scanResult && (scanResult.status === 'error' || scanResult.status === 'completed') && (
        <Card sx={{ mt: 4, borderRadius: 2, boxShadow: 2 }}>
          <CardContent sx={{ p: 4 }}>
            {scanResult.status === 'error' && (
              <Alert severity="error" sx={{ borderRadius: 2 }}>
                <Typography variant="body1" fontWeight="medium">
                  Scan Failed
                </Typography>
                <Typography variant="body2">
                  Please try again or check your configuration.
                </Typography>
              </Alert>
            )}

            {scanResult.status === 'completed' && (
              <Alert severity="success" sx={{ borderRadius: 2 }}>
                <Typography variant="body1" fontWeight="medium">
                  Scan Completed Successfully!
                </Typography>
                <Typography variant="body2">
                  Click "View Results" to see detailed results in the Sessions page.
                </Typography>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Prompt Selector Dialog */}
      <Dialog
        open={promptSelectorOpen}
        onClose={closePromptSelector}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 }
        }}
      >
        <DialogTitle sx={{ pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h5" fontWeight="bold">
              Select Individual Prompts
            </Typography>
            <IconButton
              onClick={closePromptSelector}
              sx={{ 
                color: 'text.secondary',
                '&:hover': { backgroundColor: 'grey.100' }
              }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ px: 3, pb: 2 }}>
          <TextField
            fullWidth
            placeholder="Search prompts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
            sx={{ 
              mb: 3,
              '& .MuiOutlinedInput-root': { borderRadius: 2 }
            }}
          />

          <Paper 
            variant="outlined" 
            sx={{ 
              maxHeight: 500, 
              overflow: 'auto',
              borderRadius: 2,
              backgroundColor: 'grey.50'
            }}
          >
            <List sx={{ p: 0 }}>
              {filteredPrompts.map((prompt, index) => (
                <React.Fragment key={prompt.id}>
                  <ListItem 
                    sx={{ 
                      py: 2,
                      px: 3,
                      '&:hover': { backgroundColor: 'grey.100' }
                    }}
                  >
                    <Checkbox
                      checked={selectedPrompts.includes(prompt.id)}
                      onChange={() => handlePromptToggle(prompt.id)}
                      disabled={selectedCollection.some(collectionId => {
                        const collection = collections.find(c => c.id === collectionId)
                        return collection && collection.prompt_ids && collection.prompt_ids.includes(prompt.id)
                      })}
                      sx={{ mr: 2 }}
                    />
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                          <Typography 
                            variant="body2" 
                            fontFamily="monospace"
                            sx={{ 
                              fontWeight: 600,
                              color: 'primary.main',
                              minWidth: 'fit-content'
                            }}
                          >
                            {prompt.id}
                          </Typography>
                          <Chip
                            label={prompt.attack_technique}
                            size="small"
                            variant="outlined"
                            sx={{ borderRadius: 1 }}
                          />
                          <Chip
                            label={prompt.vuln_category}
                            size="small"
                            variant="outlined"
                            sx={{ borderRadius: 1 }}
                          />
                        </Box>
                      }
                      secondary={
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            color: 'text.secondary',
                            maxWidth: '100%'
                          }}
                        >
                          {prompt.prompt}
                        </Typography>
                      }
                    />
                  </ListItem>
                  {index < filteredPrompts.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button 
            onClick={closePromptSelector}
            variant="contained"
            sx={{ 
              px: 4,
              py: 1.5,
              borderRadius: 2
            }}
          >
            Done ({individualPromptsCount} selected)
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dataset Selector Dialog */}
      <Dialog
        open={datasetSelectorOpen}
        onClose={closeDatasetSelector}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 2 }
        }}
      >
        <DialogTitle sx={{ pb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h5" fontWeight="bold">
              Select Dataset
            </Typography>
            <IconButton
              onClick={closeDatasetSelector}
              sx={{ 
                color: 'text.secondary',
                '&:hover': { backgroundColor: 'grey.100' }
              }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ px: 3, pb: 2 }}>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            Load prompts from popular datasets. Note: The first time you load a dataset, it will be downloaded from Hugging Face.
          </Typography>

          <Grid container spacing={2}>
            {/* Aegis Dataset */}
            <Grid item xs={12} md={6}>
              <Card 
                variant="outlined" 
                sx={{ 
                  p: 3, 
                  borderRadius: 2,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  border: datasetsToLoad.includes('nvidia/Aegis-AI-Content-Safety-Dataset-1.0') ? '2px solid' : '1px solid',
                  borderColor: datasetsToLoad.includes('nvidia/Aegis-AI-Content-Safety-Dataset-1.0') ? 'primary.main' : 'divider',
                  backgroundColor: datasetsToLoad.includes('nvidia/Aegis-AI-Content-Safety-Dataset-1.0') ? 'primary.50' : 'background.paper',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'primary.50'
                  }
                }}
                onClick={() => {
                  const datasetName = 'nvidia/Aegis-AI-Content-Safety-Dataset-1.0'
                  if (datasetsToLoad.includes(datasetName)) {
                    setDatasetsToLoad(prev => prev.filter(d => d !== datasetName))
                  } else {
                    setDatasetsToLoad(prev => [...prev, datasetName])
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Checkbox
                    checked={datasetsToLoad.includes('nvidia/Aegis-AI-Content-Safety-Dataset-1.0')}
                    onChange={(e) => {
                      e.stopPropagation()
                      const datasetName = 'nvidia/Aegis-AI-Content-Safety-Dataset-1.0'
                      if (e.target.checked) {
                        setDatasetsToLoad(prev => [...prev, datasetName])
                      } else {
                        setDatasetsToLoad(prev => prev.filter(d => d !== datasetName))
                      }
                    }}
                    sx={{ mt: -1, ml: -1 }}
                  />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      Aegis AI Content Safety
                    </Typography>
                    <Typography variant="caption" color="textSecondary" sx={{ mb: 2, display: 'block' }}>
                      nvidia/Aegis-AI-Content-Safety-Dataset-1.0
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ mb: 2, flexGrow: 1 }}>
                  Comprehensive dataset for testing LLM content safety across 13 critical risk categories.
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  <Chip label="Hate" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Sexual" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Violence" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="PII" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Harassment" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                </Box>
              </Card>
            </Grid>

            {/* BeaverTails Dataset */}
            <Grid item xs={12} md={6}>
              <Card 
                variant="outlined" 
                sx={{ 
                  p: 3, 
                  borderRadius: 2,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  border: datasetsToLoad.includes('PKU-Alignment/BeaverTails') ? '2px solid' : '1px solid',
                  borderColor: datasetsToLoad.includes('PKU-Alignment/BeaverTails') ? 'primary.main' : 'divider',
                  backgroundColor: datasetsToLoad.includes('PKU-Alignment/BeaverTails') ? 'primary.50' : 'background.paper',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'primary.50'
                  }
                }}
                onClick={() => {
                  const datasetName = 'PKU-Alignment/BeaverTails'
                  if (datasetsToLoad.includes(datasetName)) {
                    setDatasetsToLoad(prev => prev.filter(d => d !== datasetName))
                  } else {
                    setDatasetsToLoad(prev => [...prev, datasetName])
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Checkbox
                    checked={datasetsToLoad.includes('PKU-Alignment/BeaverTails')}
                    onChange={(e) => {
                      e.stopPropagation()
                      const datasetName = 'PKU-Alignment/BeaverTails'
                      if (e.target.checked) {
                        setDatasetsToLoad(prev => [...prev, datasetName])
                      } else {
                        setDatasetsToLoad(prev => prev.filter(d => d !== datasetName))
                      }
                    }}
                    sx={{ mt: -1, ml: -1 }}
                  />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      BeaverTails
                    </Typography>
                    <Typography variant="caption" color="textSecondary" sx={{ mb: 2, display: 'block' }}>
                      PKU-Alignment/BeaverTails
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ mb: 2, flexGrow: 1 }}>
                  Human-labeled QA pairs from 14 harm categories focused on AI safety and alignment.
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  <Chip label="Violence" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Illegal" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Discrimination" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Privacy" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  <Chip label="Misinformation" size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                </Box>
              </Card>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button 
            onClick={closeDatasetSelector}
            variant="outlined"
            sx={{ 
              px: 4,
              py: 1.5,
              borderRadius: 2
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={loadSelectedDatasets}
            variant="contained"
            disabled={loadingDataset || datasetsToLoad.length === 0}
            sx={{ 
              px: 4,
              py: 1.5,
              borderRadius: 2
            }}
          >
            {loadingDataset ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Loading...
              </>
            ) : (
              `Done (${datasetsToLoad.length} selected)`
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Scan

