import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Button
} from '@mui/material'
import { Refresh as RefreshIcon, Check as CheckIcon } from '@mui/icons-material'
import axios from 'axios'
import CustomDropdown, { DropdownOption } from '../components/common/CustomDropdown'
import SlideOverlay from '../components/common/SlideOverlay'
import { useSocket } from '../contexts/SocketContext'

interface AtlasTechnique {
  id: string
  name: string
  description: string
  tactic?: string
  tactics?: string[]
  url?: string
  violations?: number
  created_date?: string
  modified_date?: string
}

interface AtlasTactic {
  id: string
  name: string
  description: string
  techniques: AtlasTechnique[]
}

interface AtlasMatrix {
  id: string
  name: string
  tactics: AtlasTactic[]
  techniques?: any[]
}

interface AtlasData {
  id: string
  name: string
  version: string
  matrices: AtlasMatrix[]
}

interface Session {
  id: string
  name: string
  status: string
}

interface TechniqueDetails {
  technique: AtlasTechnique
  relatedPrompts: any[]
}

const MitreAtlas: React.FC = () => {
  const [atlasData, setAtlasData] = useState<AtlasData | null>(null)
  const [taxonomies, setTaxonomies] = useState<any>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTechnique, setSelectedTechnique] = useState<TechniqueDetails | null>(null)
  const [tacticMap, setTacticMap] = useState<Map<string, string>>(new Map())
  const { socket } = useSocket()

  // Utility function to clean technique descriptions
  const cleanTechniqueDescription = (description: string): string => {
    if (!description) return description
    
    // Remove ATLAS YAML references like ([Direct](/techniques/AML.T0051.000))
    // and [Journals and Conference Proceedings](/techniques/AML.T0000.000)
    // This regex matches both patterns and extracts just the text
    return description
      .replace(/\(\[([^\]]+)\]\(\/techniques\/[^)]+\)\)/g, '$1') // Pattern with parentheses
      .replace(/\[([^\]]+)\]\(\/techniques\/[^)]+\)/g, '$1')    // Pattern without parentheses
  }

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
        loadAtlasData(),
        loadAtlasTaxonomies(),
        loadSessions()
      ])
    } catch (error) {
      console.error('Error loading initial data:', error)
      setError('Failed to load MITRE ATLAS data')
    } finally {
      setLoading(false)
    }
  }

  const loadAtlasData = async () => {
    try {
      const response = await axios.get('/api/atlas-data')
      setAtlasData(response.data)
      
      // Build tactic mapping
      if (response.data.matrices && response.data.matrices.length > 0) {
        const matrix = response.data.matrices[0]
        if (matrix.tactics) {
          const newTacticMap = new Map<string, string>()
          matrix.tactics.forEach((tactic: any) => {
            newTacticMap.set(tactic.id, tactic.name)
          })
          setTacticMap(newTacticMap)
        }
      }
    } catch (error) {
      console.error('Error loading ATLAS data:', error)
      throw error
    }
  }

  const loadAtlasTaxonomies = async () => {
    try {
      const response = await axios.get('/api/atlas/taxonomies')
      setTaxonomies(response.data)
    } catch (error) {
      console.error('Failed to load ATLAS taxonomies:', error)
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
        ? '/api/atlas/taxonomies/filtered'
        : '/api/atlas/taxonomies'
      
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

  const handleTechniqueClick = async (technique: AtlasTechnique) => {
    try {
      // Get failed prompts for this technique from all sessions
      const failedPrompts = await getFailedPromptsForTechnique(technique.id)
      
      // Get the tactic name for this technique
      // Handle both single tactic and multiple tactics
      let tacticName = 'Unknown'
      if (technique.tactic) {
        // Single tactic (from backend processing)
        tacticName = tacticMap.get(technique.tactic) || technique.tactic
      } else if (technique.tactics && Array.isArray(technique.tactics) && technique.tactics.length > 0) {
        // Multiple tactics (from raw ATLAS data)
        const firstTacticId = technique.tactics[0]
        tacticName = tacticMap.get(firstTacticId) || firstTacticId
      }
      
      setSelectedTechnique({
        technique: {
          ...technique,
          tactic: tacticName
        },
        relatedPrompts: failedPrompts
      })
    } catch (error) {
      console.error('Error loading technique details:', error)
      setSelectedTechnique({
        technique,
        relatedPrompts: []
      })
    }
  }

  const getFailedPromptsForTechnique = async (techniqueId: string) => {
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
      
      // Process each session to find failed prompts for this technique
      for (const session of allSessions) {
        if (session.status === 'completed' && session.results) {
          for (const result of session.results) {
            if (result.status === 'failed' && result.prompt_id) {
              // Get the prompt details from our lookup map
              const prompt = promptMap.get(result.prompt_id)
              
              if (prompt) {
                // Check if this prompt maps to the current technique
                const atlasMappings = prompt.mitreatlasmapping || []
                if (atlasMappings.includes(techniqueId)) {
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
      console.error('Error getting failed prompts for technique:', error)
      return []
    }
  }

  const getSessionOptions = (): DropdownOption[] => {
    return (sessions || []).map(session => ({
      value: session.id,
      label: session.name,
      disabled: session.status === 'running'
    }))
  }

  const getTechniqueViolations = (techniqueId: string): number => {
    if (!taxonomies || !taxonomies.techniques) return 0
    
    // Handle both array and object formats
    if (Array.isArray(taxonomies.techniques)) {
    const technique = taxonomies.techniques.find((t: any) => t.id === techniqueId)
    return technique?.violations || 0
    } else if (typeof taxonomies.techniques === 'object') {
      // Handle object format where key is technique ID
      const technique = taxonomies.techniques[techniqueId]
      return technique?.violation_count || 0
    }
    
    return 0
  }

  const renderAtlasMatrix = () => {
    if (!atlasData || !atlasData.matrices || !atlasData.matrices[0] || !atlasData.matrices[0].tactics) {
      return (
        <Box sx={{ mt: 3, p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            Loading ATLAS data...
          </Typography>
        </Box>
      )
    }

    try {
      const atlasMatrix = atlasData.matrices[0]
      const tactics = atlasMatrix.tactics || []
      const allTechniques = atlasMatrix.techniques || []

    return (
      <Box sx={{ mt: 3 }}>

        {/* Matrix Grid Container - Horizontally Scrollable */}
        <Box sx={{ 
          overflowX: 'auto',
          overflowY: 'visible',
          pb: 2,
          '&::-webkit-scrollbar': {
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: '#f1f1f1',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#888',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: '#555',
            },
          },
        }}>
          {/* Matrix Grid */}
          <Box sx={{ 
            display: 'grid',
            gridTemplateColumns: `repeat(${tactics.length}, minmax(200px, 200px))`,
            gap: '6px',
            minWidth: 'min-content',
          }}>
          {tactics.map((tactic: AtlasTactic) => {
            // Filter techniques for this tactic (Python approach)
            const tacticTechniques = allTechniques.filter((tech: any) => 
              tech.tactics && tech.tactics.includes(tactic.id)
            )

            return (
            <Box key={tactic.id} sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              width: '100%'
            }}>
                  {/* Tactic Header */}
              <Box sx={{ 
                bgcolor: '#3f83f8', 
                color: 'white', 
                p: '8px 4px', 
                borderRadius: '4px 4px 0 0',
                textAlign: 'center',
                minHeight: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Typography variant="subtitle2" fontWeight="bold" sx={{ fontSize: '0.9rem', lineHeight: 1.1 }}>
                      {tactic.name}
                    </Typography>
                  </Box>

              {/* Technique Count */}
              <Box sx={{ 
                bgcolor: '#f8fafc', 
                border: '1px solid #e2e8f0',
                borderTop: 'none',
                p: '4px 8px',
                textAlign: 'center'
              }}>
                <Typography variant="caption" sx={{ 
                  fontSize: '0.7rem', 
                  color: '#374151',
                  fontWeight: 'medium'
                }}>
                  {tacticTechniques.length} technique{tacticTechniques.length !== 1 ? 's' : ''}
                </Typography>
              </Box>
              
              {/* Techniques Column */}
              <Box sx={{ 
                bgcolor: '#f8fafc', 
                border: '1px solid #e2e8f0',
                borderTop: 'none',
                borderRadius: '0 0 4px 4px',
                p: '4px',
                minHeight: 'auto'
              }}>
                
                {tacticTechniques.map((technique: any) => {
                  let violations = 0
                  try {
                    violations = getTechniqueViolations(technique.id)
                  } catch (error) {
                    console.error('Error getting technique violations:', error)
                    violations = 0
                  }
                      
                      return (
                    <Box
                          key={technique.id}
                            sx={{
                              cursor: 'pointer',
                        mb: '2px',
                        p: '4px',
                        borderRadius: '3px',
                        border: '1px solid #e2e8f0',
                        bgcolor: '#ffffff',
                              transition: 'all 0.2s ease',
                        position: 'relative',
                              '&:hover': {
                          borderColor: '#3f83f8',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                              },
                        '&:last-child': {
                          mb: 0
                        }
                            }}
                            onClick={() => handleTechniqueClick(technique)}
                          >
                      {violations > 0 && (
                        <Box sx={{
                          position: 'absolute',
                          top: '2px',
                          right: '2px',
                          bgcolor: '#ef4444',
                          color: 'white',
                          borderRadius: '50%',
                          width: '18px',
                          height: '18px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '0.7rem',
                          fontWeight: 'bold'
                        }}>
                          {violations}
                        </Box>
                      )}
                      
                      <Typography variant="caption" sx={{ 
                        fontSize: '0.7rem', 
                        fontWeight: 'bold',
                        color: '#374151',
                        display: 'block',
                        mb: '1px',
                        lineHeight: 1.1
                      }}>
                        {technique.id}
                      </Typography>
                      <Typography variant="body2" sx={{ 
                        fontSize: '0.8rem', 
                        lineHeight: 1.2,
                        color: '#3f83f8'
                      }}>
                                    {technique.name}
                                  </Typography>
                                </Box>
                  )
                })}
                
                {/* Fallback if no techniques */}
                {tacticTechniques.length === 0 && (
                  <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#666', fontStyle: 'italic' }}>
                    No techniques found
                  </Typography>
                                )}
                              </Box>
            </Box>
                      )
                    })}
          </Box>
        </Box>
      </Box>
    )
    } catch (error) {
      console.error('Error rendering ATLAS matrix:', error)
      return (
        <Box sx={{ mt: 3, p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="error">
            Error loading ATLAS matrix
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            {error instanceof Error ? error.message : 'Unknown error'}
          </Typography>
      </Box>
    )
    }
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
          MITRE ATLAS Navigator
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          View vulnerabilities mapped to the MITRE ATLAS framework
        </Typography>
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          right: 0,
          width: '200px',
          height: '200px'
        }}>
          <img 
            src="/api/static/mitre_atlas.png" 
            alt="MITRE ATLAS Logo" 
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

      {/* ATLAS Matrix */}
      {renderAtlasMatrix()}

      {/* Technique Details Overlay */}
      <SlideOverlay
        open={!!selectedTechnique}
        onClose={() => setSelectedTechnique(null)}
        title={selectedTechnique ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" fontWeight="bold" noWrap>
              {selectedTechnique.technique.name}
            </Typography>
            <Chip
              label={selectedTechnique.technique.id}
              color="primary"
              variant="outlined"
              size="small"
            />
          </Box>
        ) : ""}
        width={700}
        actions={
          selectedTechnique && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mr: 2 }}>
              <Chip
                label={`Tactic: ${selectedTechnique.technique.tactic || 'Unknown'}`}
              size="small"
                variant="outlined"
              />
            </Box>
          )
        }
      >
        {selectedTechnique && (
          <Box sx={{ p: 3 }}>

            {/* Technique Details */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Technique Details
              </Typography>
              <Typography variant="body1" paragraph sx={{ lineHeight: 1.6 }}>
                {cleanTechniqueDescription(selectedTechnique.technique.description)}
            </Typography>
            </Box>

            {/* External Links */}
            {selectedTechnique.technique.url && (
              <Box sx={{ mb: 3 }}>
              <Button
                  variant="contained"
                href={selectedTechnique.technique.url}
                target="_blank"
                rel="noopener noreferrer"
                  sx={{ mr: 2 }}
              >
                  View MITRE Documentation
              </Button>
              </Box>
            )}

            {/* Failed Prompts */}
            <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
                Failed Prompts ({selectedTechnique.relatedPrompts?.length || 0})
            </Typography>
            
              {!selectedTechnique.relatedPrompts || selectedTechnique.relatedPrompts.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CheckIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
              <Typography variant="body2" color="textSecondary">
                    No failed prompts found for this technique.
              </Typography>
                </Box>
            ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {(selectedTechnique.relatedPrompts || []).map((prompt: any, index: number) => (
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
          </Box>
        )}
      </SlideOverlay>
    </Box>
  )
}

export default MitreAtlas




