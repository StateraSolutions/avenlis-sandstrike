import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  LinearProgress
} from '@mui/material'
import { Refresh as RefreshIcon, Check as CheckIcon } from '@mui/icons-material'
import { motion } from 'framer-motion'
import axios from 'axios'
import CustomDropdown, { DropdownOption } from '../components/common/CustomDropdown'
import SlideOverlay from '../components/common/SlideOverlay'
import { useSocket } from '../contexts/SocketContext'

interface OwaspCategory {
  id: string
  name: string
  description: string
  violations?: number
  violation_count?: number
}


interface Session {
  id: string
  name: string
  status: string
}

interface CategoryDetails {
  category: OwaspCategory
  relatedPrompts: any[]
  markdownContent?: string
}


// OWASP LLM Top 10 categories from markdown files
const OWASP_CATEGORIES = [
  { 
    id: 'LLM01:2025', 
    name: 'Prompt Injection', 
    description: 'A Prompt Injection Vulnerability occurs when user prompts alter the LLM\'s behavior or output in unintended ways. These inputs can affect the model even if they are imperceptible to humans, therefore prompt injections do not need to be human-visible/readable, as long as the content is parsed by the model.' 
  },
  { 
    id: 'LLM02:2025', 
    name: 'Sensitive Information Disclosure', 
    description: 'Sensitive information can affect both the LLM and its application context. This includes personal identifiable information (PII), financial details, health records, confidential business data, security credentials, and legal documents.' 
  },
  { 
    id: 'LLM03:2025', 
    name: 'Supply Chain Vulnerabilities', 
    description: 'Supply chain vulnerabilities in LLM systems arise from dependencies on external components, including pre-trained models, training datasets, plugins, and third-party services that may introduce security risks.' 
  },
  { 
    id: 'LLM04:2025', 
    name: 'Data and Model Poisoning', 
    description: 'Data and model poisoning attacks involve malicious manipulation of training data or model parameters to introduce vulnerabilities, biases, or backdoors that can be exploited during inference.' 
  },
  { 
    id: 'LLM05:2025', 
    name: 'Improper Output Handling', 
    description: 'Improper output handling occurs when LLM outputs are not properly validated, sanitized, or filtered before being used by downstream systems, potentially leading to security vulnerabilities.' 
  },
  { 
    id: 'LLM06:2025', 
    name: 'Excessive Agency', 
    description: 'Excessive agency refers to LLMs being granted too much autonomy or decision-making capabilities beyond their intended scope, potentially leading to unintended consequences or security risks.' 
  },
  { 
    id: 'LLM07:2025', 
    name: 'System Prompt Leakage', 
    description: 'System prompt leakage occurs when internal system prompts, instructions, or configurations are inadvertently exposed to users, potentially revealing sensitive information about the system\'s behavior or security measures.' 
  },
  { 
    id: 'LLM08:2025', 
    name: 'Vector and Embedding Weaknesses', 
    description: 'Vector and embedding weaknesses refer to vulnerabilities in vector databases, embedding models, or similarity search mechanisms that can be exploited to manipulate retrieval results or access unauthorized information.' 
  },
  { 
    id: 'LLM09:2025', 
    name: 'Misinformation', 
    description: 'Misinformation vulnerabilities involve the generation or propagation of false, misleading, or harmful information by LLMs, which can have significant social, political, or economic consequences.' 
  },
  { 
    id: 'LLM10:2025', 
    name: 'Unbounded Consumption', 
    description: 'Unbounded consumption refers to excessive resource usage by LLMs, including computational resources, API calls, or costs, which can lead to denial of service or unexpected financial burdens.' 
  }
]

const OwaspLlm: React.FC = () => {
  const [taxonomies, setTaxonomies] = useState<any>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<CategoryDetails | null>(null)
  const { socket } = useSocket()

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (socket) {
      socket.on('session_updated', loadSessions)
      socket.on('prompt_updated', () => loadTaxonomies())
      return () => {
        socket.off('session_updated', loadSessions)
        socket.off('prompt_updated')
      }
    }
  }, [socket])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadOwaspTaxonomies(),
        loadSessions()
      ])
    } catch (error) {
      console.error('Error loading initial data:', error)
      setError('Failed to load OWASP LLM data')
    } finally {
      setLoading(false)
    }
  }

  const loadOwaspTaxonomies = async () => {
    try {
      const response = await axios.get('/api/owasp/taxonomies')
      setTaxonomies(response.data)
    } catch (error) {
      console.error('Failed to load OWASP taxonomies:', error)
      throw error
    }
  }

  const loadOwaspMarkdown = async (llmId: string) => {
    try {
      const fileMap: Record<string, string> = {
        'LLM01:2025': 'LLM01_PromptInjection.md',
        'LLM02:2025': 'LLM02_SensitiveInformationDisclosure.md',
        'LLM03:2025': 'LLM03_SupplyChain.md',
        'LLM04:2025': 'LLM04_DataModelPoisoning.md',
        'LLM05:2025': 'LLM05_ImproperOutputHandling.md',
        'LLM06:2025': 'LLM06_ExcessiveAgency.md',
        'LLM07:2025': 'LLM07_SystemPromptLeakage.md',
        'LLM08:2025': 'LLM08_VectorAndEmbeddingWeaknesses.md',
        'LLM09:2025': 'LLM09_Misinformation.md',
        'LLM10:2025': 'LLM10_UnboundedConsumption.md'
      }
      
      const filename = fileMap[llmId]
      if (!filename) {
        throw new Error(`No markdown file found for ${llmId}`)
      }
      
      const response = await axios.get(`/info/${filename}`)
      const content = response.data
      
      // Extract title from the first line (## LLM01:2025 Prompt Injection)
      const lines = content.split('\n')
      const titleLine = lines.find((line: string) => line.startsWith('## '))
      const title = titleLine ? titleLine.replace('## ', '') : `${llmId} Details`
      
      return { title, content }
    } catch (error) {
      console.error(`Failed to load markdown for ${llmId}:`, error)
      throw error
    }
  }

  const loadSessions = async () => {
    try {
      const response = await axios.get('/api/sessions')
      setSessions(response.data.sessions || [])
    } catch (error) {
      console.error('Error loading sessions:', error)
    }
  }

  const loadTaxonomies = async () => {
    try {
      const url = selectedSessions.length > 0 
        ? '/api/owasp/taxonomies/filtered'
        : '/api/owasp/taxonomies'
      
      const response = selectedSessions.length > 0
        ? await axios.post(url, { session_ids: selectedSessions })
        : await axios.get(url)
      
      setTaxonomies(response.data)
    } catch (error) {
      console.error('Error loading taxonomies:', error)
    }
  }

  useEffect(() => {
    if (sessions.length > 0) {
      loadTaxonomies()
    }
  }, [selectedSessions])

  const handleCategoryClick = async (category: OwaspCategory) => {
    try {
      // Load markdown content
      const markdownData = await loadOwaspMarkdown(category.id)
      
      // Get failed prompts for this category
      const failedPrompts = await getFailedPromptsForCategory(category.id)
      
      setSelectedCategory({
        category,
        relatedPrompts: failedPrompts,
        markdownContent: markdownData.content
      })
    } catch (error) {
      console.error('Error loading category details:', error)
      setSelectedCategory({
        category,
        relatedPrompts: []
      })
    }
  }

  const getFailedPromptsForCategory = async (categoryId: string) => {
    try {
      // Get all sessions
      const sessionsResponse = await axios.get('/api/sessions')
      const allSessions = sessionsResponse.data.sessions || []
      
      // Get all prompts to build a lookup map
      const promptsResponse = await axios.get('/api/prompts')
      const allPrompts = promptsResponse.data.prompts || []
      
      // Create a prompt lookup map for quick access
      const promptMap = new Map()
      allPrompts.forEach((prompt: any) => {
        promptMap.set(prompt.id, prompt)
      })
      
      const failedPrompts: any[] = []
      
      // Process each session to find failed prompts for this category
      for (const session of allSessions) {
        if (session.status === 'completed' && session.results) {
          for (const result of session.results) {
            if (result.status === 'failed' && result.prompt_id) {
              // Get the prompt details from our lookup map
              const prompt = promptMap.get(result.prompt_id)
              
              if (prompt) {
                // Check if this prompt maps to the current category
                const owaspMappings = prompt.owasp_top10_llm_mapping || []
                if (owaspMappings.includes(categoryId)) {
                  failedPrompts.push({
                    id: prompt.id,
                    prompt_text: prompt.prompt,
                    attack_technique: prompt.attack_technique,
                    vuln_category: prompt.vuln_category,
                    vuln_subcategory: prompt.vuln_subcategory,
                    session_id: session.id,
                    session_name: session.name
                  })
                }
              }
            }
          }
        }
      }
      
      return failedPrompts
    } catch (error) {
      console.error('Error getting failed prompts for category:', error)
      return []
    }
  }

  const getSessionOptions = (): DropdownOption[] => {
    return sessions.map(session => ({
      value: session.id,
      label: session.name,
      disabled: session.status === 'running'
    }))
  }



  const renderOwaspCards = () => {
    return (
      <Box sx={{ mt: 3 }}>
        <Grid container spacing={3}>
          {OWASP_CATEGORIES.map((category: any, index: number) => {
            const violations = taxonomies?.violation_counts?.[category.id] || 0
            
            return (
              <Grid item xs={12} sm={6} md={4} xl={2.4} key={category.id}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                   <Card
                     sx={{
                       height: '280px', // Fixed height for all cards
                       cursor: 'pointer',
                       transition: 'all 0.3s ease',
                       position: 'relative',
                       '&:hover': {
                         transform: 'translateY(-4px)',
                         boxShadow: 4
                       }
                     }}
                     onClick={() => handleCategoryClick(category)}
                   >
                     <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" fontWeight="bold" gutterBottom>
                            {category.id}: {category.name}
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Typography 
                        variant="body2" 
                        color="textSecondary" 
                        sx={{ 
                          flex: 1,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          lineHeight: 1.4,
                          maxHeight: '2.8em'
                        }}
                      >
                        {category.description}
                      </Typography>
                      
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={violations > 0 ? Math.min(violations * 10, 100) : 0}
                          color={violations > 0 ? "error" : undefined}
                          sx={{ 
                            height: 6, 
                            borderRadius: 3,
                            backgroundColor: violations === 0 ? 'grey.300' : undefined,
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: violations === 0 ? 'grey.400' : undefined
                            }
                          }}
                        />
                        <Typography 
                          variant="caption" 
                          color={violations > 0 ? "error.main" : "text.secondary"} 
                          sx={{ mt: 0.5, display: 'block' }}
                        >
                          {violations > 0 ? `${violations} violation${violations !== 1 ? 's' : ''}` : 'No violations'}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            )
          })}
        </Grid>
      </Box>
    )
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={loadInitialData} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Box mb={4} sx={{ position: 'relative' }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          OWASP LLM Top 10 (2025)
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          View vulnerabilities mapped to the OWASP LLM Top 10 2025 framework
        </Typography>
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          right: 0,
          width: '200px',
          height: '200px'
        }}>
          <img 
            src="/api/static/owasp_llm.png" 
            alt="OWASP LLM Logo" 
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'contain' 
            }}
          />
        </Box>
      </Box>

      {/* Session Filter */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <CustomDropdown
          label="Filter by Session"
          options={getSessionOptions()}
          selectedValues={selectedSessions}
          onChange={setSelectedSessions}
          placeholder="All sessions"
          maxWidth={400}
        />
      </Box>

      {/* OWASP Cards */}
      {renderOwaspCards()}

      {/* Category Details Overlay */}
      <SlideOverlay
        open={!!selectedCategory}
        onClose={() => setSelectedCategory(null)}
        title={selectedCategory ? `${selectedCategory.category.id} ${selectedCategory.category.name}` : ""}
        width={700}
      >
        {selectedCategory && (
          <Box sx={{ p: 3 }}>
            {/* Markdown Content */}
            {selectedCategory.markdownContent && (
              <Box sx={{ mb: 3 }}>
                <Box sx={{ 
                  '& h1': { fontSize: '1.5rem', fontWeight: 'bold', mb: 2, mt: 3 },
                  '& h2': { fontSize: '1.25rem', fontWeight: 'bold', mb: 1.5, mt: 2 },
                  '& h3': { fontSize: '1.3rem', fontWeight: 'bold', mb: 1, mt: 2.5 },
                  '& h3:first-of-type': { mt: 0 }, // Remove top gap from first h3
                  '& h4': { fontSize: '1rem', fontWeight: 'bold', mb: 0.25, mt: 2.5 },
                  '& p': { mb: 1.5, lineHeight: 1.6 },
                  '& ul': { mb: 1.5, pl: 4 },
                  '& ol': { mb: 1.5, pl: 2 },
                  '& li': { mb: 0.5, pl: 2 },
                  '& code': { 
                    backgroundColor: 'grey.100', 
                    padding: '2px 4px', 
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    fontFamily: 'monospace'
                  },
                  '& pre': { 
                    backgroundColor: 'grey.100', 
                    padding: '12px', 
                    borderRadius: '8px',
                    overflow: 'auto',
                    mb: 1.5
                  },
                  '& blockquote': {
                    borderLeft: '4px solid',
                    borderColor: 'primary.main',
                    pl: 2,
                    ml: 0,
                    fontStyle: 'italic',
                    mb: 1.5
                  },
                  '& a': {
                    color: 'primary.main',
                    textDecoration: 'underline',
                    '&:hover': {
                      color: 'primary.dark',
                      textDecoration: 'none'
                    }
                  }
                }}>
                  <Typography 
                    variant="body2" 
                    component="div"
                    sx={{ whiteSpace: 'pre-wrap' }}
                    dangerouslySetInnerHTML={{ 
                      __html: selectedCategory.markdownContent
                        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                        .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
                        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
                        .replace(/`(.*?)`/gim, '<code>$1</code>')
                        .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
                        .replace(/^- (.*$)/gim, '<li>$1</li>')
                        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
                        .replace(/(https?:\/\/[^\s]+)/gim, '<a href="$1" target="_blank" rel="noopener noreferrer">[$1]</a>')
                        .replace(/\[(https?:\/\/[^\s]+)\]/gim, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
                        .replace(/\n\n/gim, '</p><p>')
                        .replace(/^(?!<[h|l|b])/gim, '<p>')
                        .replace(/(?<!>)$/gim, '</p>')
                        .replace(/^<h1>.*?<\/h1>/gim, '') // Remove first h1 title
                        .replace(/^<strong>.*?<\/strong>/gim, '') // Remove first bolded line
                        .replace(/^<h2>LLM\d+:2025.*?<\/h2>/gim, '') // Remove second LLM0X heading
                        .replace(/^<p>(A Prompt Injection Vulnerability occurs when user prompts alter the LLM's behavior|Sensitive information can affect both the LLM and its application context|Supply chain vulnerabilities in LLM systems arise from dependencies|Data and model poisoning attacks involve malicious manipulation|Improper output handling occurs when LLM outputs are not properly validated|Excessive agency refers to LLMs being granted too much autonomy|System prompt leakage occurs when internal system prompts|Vector and embedding weaknesses refer to vulnerabilities|Misinformation vulnerabilities involve the generation|Unbounded consumption refers to excessive resource usage).*?<\/p>/gim, '') // Remove first description paragraph
                        .replace(/^.*?(?=<h2>Description<\/h2>)/gims, '') // Remove everything before Description heading
                        .replace(/^<p>.*?<\/p>(?=<h2>Description<\/h2>)/gims, '') // Remove first paragraph before Description
                    }}
                  />
                </Box>
              </Box>
            )}

            <Typography variant="h6" gutterBottom>
              Failed Prompts ({selectedCategory.relatedPrompts.length})
            </Typography>
            
            {selectedCategory.relatedPrompts.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CheckIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                <Typography variant="body2" color="textSecondary">
                  No failed prompts found for this category.
            </Typography>
          </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {selectedCategory.relatedPrompts.map((prompt: any, index: number) => (
                  <Card key={prompt.id || index} variant="outlined">
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {prompt.id || `Prompt ${index + 1}`}
                        </Typography>
                        {prompt.session_name && (
                          <Chip
                            label={`Session: ${prompt.session_name}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                      
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        {prompt.prompt_text || prompt.text || prompt.prompt}
                      </Typography>
                      
                      {prompt.vuln_subcategory && (
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                          <Chip
                            label={`Subcategory: ${prompt.vuln_subcategory}`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      )}
        </CardContent>
      </Card>
                ))}
              </Box>
            )}
          </Box>
        )}
      </SlideOverlay>
    </Box>
  )
}

export default OwaspLlm
