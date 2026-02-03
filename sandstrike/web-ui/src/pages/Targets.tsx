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
  MenuItem,
  Select,
  FormControl,
  InputLabel
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

interface Target {
  id: string
  name: string
  ip_address: string
  description?: string
  target_type?: string
  model?: string
  created_at?: string
  updated_at?: string
  date_updated?: string
  source?: string
}

const Targets: React.FC = () => {
  const [targets, setTargets] = useState<Target[]>([])
  const [loading, setLoading] = useState(true)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editingTarget, setEditingTarget] = useState<Target | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [hoveredTargetId, setHoveredTargetId] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    ip_address: '',
    description: '',
    target_type: 'URL' as 'Ollama' | 'URL',
    model: '',
    source: 'local' as 'local' | 'file'
  })

  useEffect(() => {
    loadTargets()
  }, [])

  const loadTargets = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/targets')
      setTargets(response.data.targets || [])
    } catch (error) {
      console.error('Failed to load targets:', error)
    } finally {
      setLoading(false)
    }
  }

  const deleteTarget = async (targetId: string) => {
    if (!confirm('Are you sure you want to delete this target?')) return
    
    try {
      await axios.delete(`/api/targets/${targetId}`)
      await loadTargets()
    } catch (error) {
      console.error('Failed to delete target:', error)
      alert('Failed to delete target')
    }
  }

  const openCreateModal = () => {
    setFormData({
      id: '',
      name: '',
      ip_address: '',
      description: '',
      target_type: 'URL',
      model: '',
      source: 'local'
    })
    setEditingTarget(null)
    setCreateModalOpen(true)
  }

  const openEditModal = (target: Target) => {
    setFormData({
      id: target.id,
      name: target.name,
      ip_address: target.ip_address,
      description: target.description || '',
      target_type: (target.target_type || 'URL') as 'Ollama' | 'URL',
      model: target.model || '',
      source: target.source || 'local'
    })
    setEditingTarget(target)
    setCreateModalOpen(true)
  }

  const handleSaveTarget = async () => {
    if (!formData.id || !formData.name || !formData.ip_address) {
      alert('Please fill in all required fields (ID, Name, IP Address)')
      return
    }

    // Validate model is provided for Ollama targets
    if (formData.target_type === 'Ollama' && !formData.model) {
      alert('Model name is required for Ollama targets')
      return
    }

    try {
      const data = {
        ...formData,
        // Only include model if target_type is Ollama
        model: formData.target_type === 'Ollama' ? formData.model : undefined
      }

      if (editingTarget) {
        await axios.put(`/api/targets/${editingTarget.id}`, data)
      } else {
        await axios.post('/api/targets', data)
      }
      
      setCreateModalOpen(false)
      await loadTargets()
    } catch (error: any) {
      console.error('Failed to save target:', error)
      alert(error.response?.data?.error || 'Failed to save target')
    }
  }

  const filteredTargets = targets.filter(target =>
    target.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (target.description || '').toLowerCase().includes(searchTerm.toLowerCase())
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
      <Box mb={4} display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Scan Targets
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Manage and organize your scan targets for reusable testing
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={openCreateModal}
          sx={{ height: 'fit-content' }}
        >
          Create Target
        </Button>
      </Box>

      {/* Search Bar */}
      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search targets by name, ID, IP address, or description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ mb: 2 }}
        />
      </Box>

      {/* Targets Grid */}
      {filteredTargets.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            {searchTerm ? 'No targets found matching your search' : 'No targets found'}
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            {searchTerm ? 'Try adjusting your search terms' : 'Create your first target to get started'}
          </Typography>
          {!searchTerm && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openCreateModal}
            >
              Create Target
            </Button>
          )}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredTargets.map((target, index) => (
            <Grid item xs={12} sm={6} md={4} key={target.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card
                  onMouseEnter={() => setHoveredTargetId(target.id)}
                  onMouseLeave={() => setHoveredTargetId(null)}
                  sx={{
                    height: '100%',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Chip
                        label={target.source === 'file' ? 'File' : 'Local'}
                        size="small"
                        color={target.source === 'file' ? 'primary' : 'secondary'}
                        variant="outlined"
                      />
                      <Box
                        sx={{
                          opacity: hoveredTargetId === target.id ? 1 : 0,
                          transition: 'opacity 0.2s ease-in-out',
                          display: 'flex',
                          gap: 0.5
                        }}
                      >
                        <CustomTooltip title="Edit Target">
                          <IconButton
                            size="small"
                            color="info"
                            onClick={() => openEditModal(target)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </CustomTooltip>
                        <CustomTooltip title="Delete Target">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => deleteTarget(target.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </CustomTooltip>
                      </Box>
                    </Box>
                    
                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                      {target.name}
                    </Typography>
                    
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                      <strong>ID:</strong> {target.id}
                    </Typography>
                    
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                      <strong>IP Address:</strong> {target.ip_address}
                    </Typography>
                    
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                      <strong>Type:</strong> {target.target_type || 'URL'}
                    </Typography>
                    
                    {target.target_type === 'Ollama' && target.model && (
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        <strong>Model:</strong> {target.model}
                      </Typography>
                    )}
                    
                    {target.description && (
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          mt: 1
                        }}
                      >
                        {target.description}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTarget ? 'Edit Target' : 'Create New Target'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Target ID"
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value })}
              required
              disabled={!!editingTarget}
              helperText={editingTarget ? 'Target ID cannot be changed' : 'Unique identifier for the target'}
              fullWidth
            />
            <TextField
              label="Target Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="IP Address"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              required
              helperText="IP address or URL (may include port, e.g., 192.168.1.1:8080)"
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Target Type</InputLabel>
              <Select
                value={formData.target_type}
                onChange={(e) => setFormData({ ...formData, target_type: e.target.value as 'Ollama' | 'URL', model: e.target.value === 'URL' ? '' : formData.model })}
                label="Target Type"
              >
                <MenuItem value="URL">URL</MenuItem>
                <MenuItem value="Ollama">Ollama</MenuItem>
              </Select>
            </FormControl>
            {formData.target_type === 'Ollama' && (
              <TextField
                label="Model Name"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                required
                helperText="Ollama model name (e.g., llama2, mistral, codellama)"
                placeholder="llama2, mistral, codellama"
                fullWidth
              />
            )}
            <TextField
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />
            {!editingTarget && (
              <FormControl fullWidth>
                <InputLabel>Source</InputLabel>
                <Select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value as 'local' | 'file' })}
                  label="Source"
                >
                  <MenuItem value="local">Local (SQLite Database)</MenuItem>
                  <MenuItem value="file">File (YAML)</MenuItem>
                </Select>
              </FormControl>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveTarget} variant="contained">
            {editingTarget ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Targets

