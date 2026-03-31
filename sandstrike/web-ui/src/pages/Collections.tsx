import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  Paper,
  Divider,
  Fab
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import axios from 'axios'
import CustomTooltip from '../components/common/CustomTooltip'
import SlideOverlay from '../components/common/SlideOverlay'
import { useSocket } from '../contexts/SocketContext'

interface Collection {
  id: string
  name: string
  description: string
  prompt_ids: string[]
  created_at?: string
  updated_at?: string
  prompt_count?: number
  source?: string
  type?: string
}

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

const Collections: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([])
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null)
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null)
  const { socket } = useSocket()

  // Utility function to format text: capitalize first letter and replace underscores with spaces
  const formatText = (text: string | null | undefined): string => {
    if (!text) return 'N/A'
    return text
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_ids: [] as string[],
    source: 'local' as 'local' | 'file'
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (socket) {
      socket.on('collection_updated', loadCollections)
      socket.on('collection_created', loadCollections)
      socket.on('collection_deleted', loadCollections)
      return () => {
        socket.off('collection_updated', loadCollections)
        socket.off('collection_created', loadCollections)
        socket.off('collection_deleted', loadCollections)
      }
    }
  }, [socket])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      await Promise.all([loadCollections(), loadPrompts()])
    } catch (error) {
      console.error('Failed to load initial data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCollections = async () => {
    try {
      const response = await axios.get('/api/collections')
      setCollections(response.data.collections || [])
    } catch (error) {
      console.error('Failed to load collections:', error)
    }
  }

  const loadPrompts = async () => {
    try {
      const response = await axios.get('/api/prompts')
      setPrompts(response.data.prompts || [])
    } catch (error) {
      console.error('Failed to load prompts:', error)
    }
  }

  const deleteCollection = async (collectionId: string) => {
    if (!confirm('Are you sure you want to delete this collection?')) return
    
    try {
      await axios.delete(`/api/collections/${collectionId}`)
      await loadCollections()
    } catch (error) {
      console.error('Failed to delete collection:', error)
      alert('Failed to delete collection')
    }
  }

  const openCreateModal = () => {
    setFormData({
      name: '',
      description: '',
      prompt_ids: [],
      source: 'local'
    })
    setSelectedPrompts([])
    setEditingCollection(null)
    setCreateModalOpen(true)
  }

  const openEditModal = (collection: Collection) => {
    setFormData({
      name: collection.name,
      description: collection.description,
      prompt_ids: collection.prompt_ids,
      source: collection.source || 'local'
    })
    setSelectedPrompts(collection.prompt_ids)
    setEditingCollection(collection)
    setCreateModalOpen(true)
  }

  const viewCollection = (collection: Collection) => {
    setSelectedCollection(collection)
  }

  const handleSaveCollection = async () => {
    try {
      const data = {
        ...formData,
        prompt_ids: selectedPrompts
      }

      if (editingCollection) {
        await axios.put(`/api/collections/${editingCollection.id}`, data)
      } else {
        await axios.post('/api/collections', data)
      }
      
      setCreateModalOpen(false)
      await loadCollections()
    } catch (error) {
      console.error('Failed to save collection:', error)
      alert('Failed to save collection')
    }
  }

  const handlePromptToggle = (promptId: string) => {
    setSelectedPrompts(prev => 
      prev.includes(promptId)
        ? prev.filter(id => id !== promptId)
        : [...prev, promptId]
    )
  }

  const filteredPrompts = prompts.filter(prompt =>
    prompt.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    prompt.attack_technique.toLowerCase().includes(searchTerm.toLowerCase()) ||
    prompt.prompt_text.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box mb={4}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Prompt Collections
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Organize and manage your adversarial prompts
        </Typography>
      </Box>

      {/* Collections Grid */}
      <Grid container spacing={3}>
        {collections.map((collection, index) => (
          <Grid item xs={12} sm={6} md={4} key={collection.id}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4
                  }
                }}
                onClick={() => viewCollection(collection)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'flex-start', mb: 2 }}>
                    <Chip
                      label={`${collection.prompt_count || collection.prompt_ids.length} prompts`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="h6" fontWeight="bold" gutterBottom>
                    {collection.name}
                  </Typography>
                  
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      minHeight: 60
                    }}
                  >
                    {collection.description}
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <CustomTooltip title="Edit Collection">
                      <IconButton
                        size="small"
                        color="info"
                        onClick={(e) => {
                          e.stopPropagation()
                          openEditModal(collection)
                        }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </CustomTooltip>

                    <CustomTooltip title="Delete Collection">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteCollection(collection.id)
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </CustomTooltip>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}

        {/* Add New Collection Card */}
        <Grid item xs={12} sm={6} md={4}>
          <Card
            sx={{
              height: '100%',
              cursor: 'pointer',
              border: '2px dashed',
              borderColor: 'primary.main',
              transition: 'all 0.3s ease',
              '&:hover': {
                bgcolor: 'action.hover'
              }
            }}
            onClick={openCreateModal}
          >
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <AddIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" color="primary.main" textAlign="center">
                Create New Collection
              </Typography>
              <Typography variant="body2" color="textSecondary" textAlign="center" mt={1}>
                Group prompts together for organized testing
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={openCreateModal}
      >
        <AddIcon />
      </Fab>

      {/* Create/Edit Collection Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingCollection ? 'Edit Collection' : 'Create New Collection'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Collection Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={2}
              fullWidth
            />

            <TextField
              select
              label="Source Type"
              value={formData.source}
              onChange={(e) => setFormData({ ...formData, source: e.target.value as 'local' | 'file' })}
              fullWidth
              SelectProps={{
                native: true,
              }}
            >
              <option value="local">Local Database (SQLite)</option>
              <option value="file">YAML File</option>
            </TextField>

            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Select Prompts ({selectedPrompts.length} selected)
            </Typography>

            <TextField
              placeholder="Search prompts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
              size="small"
              sx={{ mb: 1 }}
            />

            <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto' }}>
              <List dense>
                {filteredPrompts.map((prompt) => (
                  <ListItem
                    key={prompt.id}
                    button
                    onClick={() => handlePromptToggle(prompt.id)}
                  >
                    <Checkbox
                      checked={selectedPrompts.includes(prompt.id)}
                      tabIndex={-1}
                      disableRipple
                    />
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontFamily="monospace">
                            {prompt.id}
                          </Typography>
                          <Chip
                            label={prompt.attack_technique}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Typography
                          variant="caption"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {prompt.prompt_text}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveCollection}
            disabled={!formData.name}
          >
            {editingCollection ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Collection Details Overlay */}
      {selectedCollection && (
        <SlideOverlay
          open={!!selectedCollection}
          onClose={() => setSelectedCollection(null)}
          title={selectedCollection.name}
        >
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              Description
            </Typography>
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="body1" color="textSecondary" sx={{ whiteSpace: 'pre-wrap' }}>
                  {selectedCollection.description || 'No description provided.'}
                </Typography>
              </CardContent>
            </Card>
            
            <Typography variant="h6" gutterBottom>
              Prompts in Collection ({selectedCollection.prompt_count || selectedCollection.prompt_ids.length})
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {selectedCollection.prompt_ids.map((promptId, index) => {
                const prompt = prompts.find(p => p.id === promptId)
                return (
                  <Card key={promptId} variant="outlined" sx={{ p: 2 }}>
                    {prompt ? (
                      <Box>
                        {/* Header: Prompt ID and Source */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="subtitle2" fontFamily="monospace" color="primary">
                            {prompt.id}
                          </Typography>
                          {prompt.source && (
                            <Chip 
                              label={prompt.source === 'file' ? 'File' : 'Local'} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                        </Box>

                        {/* Prompt Details Grid */}
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                          <Grid item xs={12} sm={6}>
                            <Typography variant="caption" color="textSecondary" display="block">
                              Attack Technique
                            </Typography>
                            <Typography variant="body2">
                              {formatText(prompt.attack_technique)}
                            </Typography>
                          </Grid>
                          
                          <Grid item xs={12} sm={6}>
                            <Typography variant="caption" color="textSecondary" display="block">
                              Vulnerability Category
                            </Typography>
                            <Typography variant="body2">
                              {formatText(prompt.vuln_category)}
                            </Typography>
                          </Grid>

                          {prompt.vuln_subcategory && (
                            <Grid item xs={12} sm={6}>
                              <Typography variant="caption" color="textSecondary" display="block">
                                Vulnerability Subcategory
                              </Typography>
                              <Typography variant="body2">
                                {formatText(prompt.vuln_subcategory)}
                              </Typography>
                            </Grid>
                          )}

                          {prompt.severity && (
                            <Grid item xs={12} sm={6}>
                              <Typography variant="caption" color="textSecondary" display="block">
                                Severity
                              </Typography>
                              <Chip 
                                label={formatText(prompt.severity)} 
                                size="small"
                                color={
                                  prompt.severity === 'critical' ? 'error' :
                                  prompt.severity === 'high' ? 'warning' :
                                  prompt.severity === 'medium' ? 'info' : 'default'
                                }
                              />
                            </Grid>
                          )}
                        </Grid>

                        {/* MITRE ATLAS Mapping */}
                        {prompt.mitreatlasmapping && prompt.mitreatlasmapping.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 0.5 }}>
                              MITRE ATLAS Mapping
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {prompt.mitreatlasmapping.map((mapping) => (
                                <Chip
                                  key={mapping}
                                  label={mapping}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}

                        {/* OWASP LLM Mapping */}
                        {prompt.owasp_top10_llm_mapping && prompt.owasp_top10_llm_mapping.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 0.5 }}>
                              OWASP Top 10 for LLM Mapping
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {prompt.owasp_top10_llm_mapping.map((mapping) => (
                                <Chip
                                  key={mapping}
                                  label={mapping}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.7rem' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}

                        {/* Prompt Text */}
                        <Box>
                          <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 0.5 }}>
                            Prompt Text
                          </Typography>
                          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50' }}>
                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {prompt.prompt}
                            </Typography>
                          </Paper>
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 2 }}>
                        <Typography variant="body2" color="textSecondary">
                          Prompt ID: {promptId}
                        </Typography>
                        <Typography variant="caption" color="error">
                          Prompt not found in database
                        </Typography>
                      </Box>
                    )}
                  </Card>
                )
              })}
            </Box>
          </Box>
        </SlideOverlay>
      )}
    </Box>
  )
}

export default Collections