import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  TextField
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  Download as DownloadIcon,
  Assessment as AssessmentIcon,
  Description as DescriptionIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Language as HtmlIcon
} from '@mui/icons-material';
import axios from 'axios';
import { formatDateTime } from '../utils/dateFormat';

interface Session {
  id: string;
  name: string;
  status: string;
  createdAt: string;
  totalPrompts: number;
  passedPrompts: number;
  failedPrompts: number;
  errorPrompts: number;
  target?: string;
  targetModel?: string;
  vulnerabilitiesFound?: number;
  tags?: string[];
  source?: string;
}

interface ReportType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

const reportTypes: ReportType[] = [
  {
    id: 'overview',
    name: 'Overview Report',
    description: 'High-level summary of security testing results with key metrics and trends',
    icon: <AssessmentIcon />,
    color: '#1976d2'
  },
  {
    id: 'detailed',
    name: 'Detailed Report',
    description: 'Comprehensive analysis with detailed findings, vulnerabilities, and recommendations',
    icon: <DescriptionIcon />,
    color: '#388e3c'
  },
  {
    id: 'executive',
    name: 'Executive Summary',
    description: 'Concise summary for leadership with business impact and strategic recommendations',
    icon: <BusinessIcon />,
    color: '#f57c00'
  }
];

const Reports: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [selectedReportType, setSelectedReportType] = useState<string>('');
  const [isPaidUser, setIsPaidUser] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [nameFilter, setNameFilter] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    checkPaidUserStatus();
    loadSessions();
  }, []);

  const checkPaidUserStatus = async () => {
    try {
      const response = await axios.get('/api/auth/status');
      setIsPaidUser(response.data.isPaidUser);
    } catch (error) {
      console.error('Error checking paid user status:', error);
      setIsPaidUser(false);
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const response = await axios.get('/api/sessions');
      const rawSessions = response.data.sessions || response.data || [];
      
      // Transform sessions to match the expected format
      const transformedSessions = rawSessions.map((session: any) => {
        // Calculate test counts from results if available
        const results = session.results || [];
        const totalPrompts = results.length;
        const passedPrompts = results.filter((r: any) => r.status === 'passed').length;
        const failedPrompts = results.filter((r: any) => r.status === 'failed').length;
        const errorPrompts = results.filter((r: any) => r.status === 'error').length;
        
        // Get date from various possible fields
        const dateValue = session.started_at || session.created_at || session.date;
        
        return {
          id: session.id,
          name: session.name || session.session_name || 'Unnamed Session',
          status: session.status,
          createdAt: dateValue,
          totalPrompts: totalPrompts,
          passedPrompts: passedPrompts,
          failedPrompts: failedPrompts,
          errorPrompts: errorPrompts,
          target: session.target || session.target_url,
          targetModel: session.target_model,
          vulnerabilitiesFound: session.vulnerabilities_found || session.vulnerabilitiesFound || failedPrompts,
          source: session.source || 'file',
          tags: session.tags || []
        };
      });
      
      setSessions(transformedSessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
      setError('Failed to load sessions');
    }
  };

  const handleSessionToggle = (sessionId: string) => {
    setSelectedSessions(prev => 
      prev.includes(sessionId) 
        ? prev.filter(id => id !== sessionId)
        : [...prev, sessionId]
    );
  };

  const handleSelectAll = () => {
    const filteredSessions = (sessions || []).filter(session => {
      const matchesName = !nameFilter || session.name.toLowerCase().includes(nameFilter.toLowerCase());
      const matchesSource = !sourceFilter || session.source === sourceFilter;
      const matchesStatus = !statusFilter || session.status === statusFilter;
      return matchesName && matchesSource && matchesStatus;
    });
    
    const filteredSessionIds = filteredSessions.map(s => s.id);
    setSelectedSessions(filteredSessionIds);
  };

  const handleGenerateReport = async () => {
    if (!selectedSessions.length || !selectedReportType) {
      setError('Please select sessions and report type');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const endpoint = '/api/reports/generate';
      const response = await axios.post(endpoint, {
        sessionIds: selectedSessions,
        reportType: selectedReportType
      }, {
        responseType: 'blob'
      });

      // Create download link for HTML file
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/html' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sandstrike-${selectedReportType}-report-${new Date().toISOString().split('T')[0]}.html`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setDialogOpen(false);
    } catch (error: any) {
      console.error('Error generating report:', error);
      setError(error.response?.data?.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <WarningIcon color="warning" />;
      default:
        return <TimelineIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!isPaidUser) {
    return (
      <Box p={3}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Reports Feature - Avenlis Pro Users Only
          </Typography>
          <Typography>
            The Reports feature is available only for Avenlis Pro users. <a 
              href="https://staterasolv.com/pricing" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: '#1976d2', textDecoration: 'underline' }}
            >
              Upgrade your account
            </a> to access comprehensive HTML reports including Overview, Detailed, and Executive Summary reports.
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            <SecurityIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
            Reports
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Generate comprehensive HTML reports from your security testing sessions
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Report Types */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Types
              </Typography>
              <List>
                {reportTypes.map((report) => (
                  <ListItem
                    key={report.id}
                    button
                    selected={selectedReportType === report.id}
                    onClick={() => setSelectedReportType(report.id)}
                    sx={{
                      borderRadius: 1,
                      mb: 1,
                      '&.Mui-selected': {
                        backgroundColor: `${report.color}20`,
                        '&:hover': {
                          backgroundColor: `${report.color}30`,
                        },
                      },
                    }}
                  >
                    <ListItemIcon sx={{ color: report.color }}>
                      {report.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={report.name}
                      secondary={report.description}
                    />
                  </ListItem>
                ))}
              </List>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
                Please select the report type you want to generate
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Sessions Selection */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Sessions ({selectedSessions.length} selected)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Choose the sessions you want to include in your report
              </Typography>
              
              {/* Filter Fields */}
              <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <TextField
                  placeholder="Filter by session name..."
                  value={nameFilter}
                  onChange={(e) => setNameFilter(e.target.value)}
                  size="small"
                  sx={{ minWidth: 200 }}
                />
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Source</InputLabel>
                  <Select
                    value={sourceFilter}
                    label="Source"
                    onChange={(e) => setSourceFilter(e.target.value)}
                  >
                    <MenuItem value="">All Sources</MenuItem>
                    <MenuItem value="local">Local</MenuItem>
                    <MenuItem value="file">File</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={statusFilter}
                    label="Status"
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <MenuItem value="">All Statuses</MenuItem>
                    <MenuItem value="completed">Completed</MenuItem>
                    <MenuItem value="running">Running</MenuItem>
                    <MenuItem value="failed">Failed</MenuItem>
                  </Select>
                </FormControl>
                <Box sx={{ flex: 1 }} />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleSelectAll}
                  sx={{ minWidth: 100 }}
                >
                  Select All
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    setNameFilter('');
                    setSourceFilter('');
                    setStatusFilter('');
                  }}
                  sx={{ minWidth: 100 }}
                >
                  Clear Filters
                </Button>
              </Box>
              
              <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
                <List>
                  {(sessions || [])
                    .filter(session => {
                      const matchesName = !nameFilter || session.name.toLowerCase().includes(nameFilter.toLowerCase());
                      const matchesSource = !sourceFilter || session.source === sourceFilter;
                      const matchesStatus = !statusFilter || session.status === statusFilter;
                      return matchesName && matchesSource && matchesStatus;
                    })
                    .map((session, index) => (
                    <React.Fragment key={session.id}>
                      <ListItem
                        button
                        onClick={() => handleSessionToggle(session.id)}
                        selected={selectedSessions.includes(session.id)}
                        sx={{
                          '&.Mui-selected': {
                            backgroundColor: '#f5f5f5',
                            '&:hover': {
                              backgroundColor: '#e0e0e0',
                            },
                          },
                        }}
                      >
                        <ListItemIcon>
                          {selectedSessions.includes(session.id) ? (
                            <Box
                              sx={{
                                width: 20,
                                height: 20,
                                borderRadius: '50%',
                                backgroundColor: 'success.main',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontSize: '12px'
                              }}
                            >
                              ✓
                            </Box>
                          ) : (
                            <Box
                              sx={{
                                width: 20,
                                height: 20,
                                borderRadius: '50%',
                                border: '2px solid',
                                borderColor: 'action.disabled',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}
                            />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={session.name}
                          secondary={
                            <Box>
                              <Typography variant="body2" component="span">
                                Created: {session.createdAt ? formatDateTime(session.createdAt) : 'Unknown Date'}
                              </Typography>
                              {session.target && (
                                <Typography variant="body2" component="span" sx={{ display: 'block', color: 'text.secondary' }}>
                                  Target: {session.target.length > 50 ? session.target.substring(0, 50) + '...' : session.target}
                                </Typography>
                              )}
                              <Box sx={{ mt: 0.5 }}>
                                <Chip
                                  label={`${session.totalPrompts || 0} Total`}
                                  size="small"
                                  variant="outlined"
                                  sx={{ mr: 1 }}
                                />
                                <Chip
                                  label={`${session.passedPrompts || 0} Passed`}
                                  size="small"
                                  color="success"
                                  sx={{ mr: 1 }}
                                />
                                <Chip
                                  label={`${session.failedPrompts || 0} Failed`}
                                  size="small"
                                  color="error"
                                  sx={{ mr: 1 }}
                                />
                                <Chip
                                  label={session.status}
                                  size="small"
                                  color={getStatusColor(session.status) as any}
                                />
                              </Box>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < sessions.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Paper>

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={<HtmlIcon />}
                  onClick={() => setDialogOpen(true)}
                  disabled={!selectedSessions.length || !selectedReportType}
                  size="large"
                >
                  Generate Report
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Generate Report Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Generate {reportTypes.find(r => r.id === selectedReportType)?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            You are about to generate <strong>{reportTypes.find(r => r.id === selectedReportType)?.name}</strong> for <strong>{selectedSessions.length}</strong> selected session{selectedSessions.length !== 1 ? 's' : ''}.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            The report will be downloaded as an HTML file once generation is complete. You can open it in any web browser.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={generating}>
            Cancel
          </Button>
          <Button
            onClick={handleGenerateReport}
            variant="contained"
            startIcon={generating ? <CircularProgress size={20} /> : <DownloadIcon />}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate & Download'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Reports;
