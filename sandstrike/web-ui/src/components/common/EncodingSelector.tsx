import React, { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Typography,
  Paper,
  Grid,
  Button,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface EncodingMethod {
  value: string;
  label: string;
  category: string;
  description: string;
}

const ENCODING_METHODS: EncodingMethod[] = [
  // Base Encodings
  { value: 'base2', label: 'Base2', category: 'Base', description: 'Binary encoding' },
  { value: 'base8', label: 'Base8', category: 'Base', description: 'Octal encoding' },
  { value: 'base16', label: 'Base16', category: 'Base', description: 'Hexadecimal encoding' },
  { value: 'base32', label: 'Base32', category: 'Base', description: 'Base32 encoding' },
  { value: 'base64', label: 'Base64', category: 'Base', description: 'Base64 encoding' },
  { value: 'base85', label: 'Base85', category: 'Base', description: 'Base85 encoding' },
  
  // ROT Encodings
  { value: 'rot5', label: 'ROT5', category: 'ROT', description: 'Rotate digits 0-9 by 5' },
  { value: 'rot13', label: 'ROT13', category: 'ROT', description: 'Rotate letters by 13' },
  { value: 'rot18', label: 'ROT18', category: 'ROT', description: 'ROT13 for letters + ROT5 for digits' },
  { value: 'rot25', label: 'ROT25', category: 'ROT', description: 'Rotate letters by 25 (ROT-1)' },
  { value: 'rot32', label: 'ROT32', category: 'ROT', description: 'Rotate printable ASCII by 32' },
  { value: 'rot47', label: 'ROT47', category: 'ROT', description: 'Rotate printable ASCII by 47' },
  
  // Special Encodings
  { value: 'hexadecimal', label: 'Hexadecimal', category: 'Special', description: 'Hex formatting' },
  { value: 'md5_hash', label: 'MD5 Hash', category: 'Special', description: 'MD5 hash generation' },
  { value: 'reverse', label: 'Reverse', category: 'Special', description: 'Text reversal' },
  { value: 'url_encode', label: 'URL Encode', category: 'Special', description: 'URL encoding' },
  { value: 'morse_code', label: 'Morse Code', category: 'Special', description: 'Morse code conversion' },
  { value: 'nato_phonetic', label: 'NATO Phonetic', category: 'Special', description: 'NATO phonetic alphabet' },
  { value: 'diacritics', label: 'Diacritics', category: 'Special', description: 'Diacritic character substitution' },
  { value: 'braille', label: 'Braille', category: 'Special', description: 'Braille character conversion' }
];

interface EncodingSelectorProps {
  selectedMethods: string[];
  onMethodsChange: (methods: string[]) => void;
  disabled?: boolean;
}

const EncodingSelector: React.FC<EncodingSelectorProps> = ({
  selectedMethods,
  onMethodsChange,
  disabled = false
}) => {
  const [showPreview, setShowPreview] = useState(false);
  const [previewText, setPreviewText] = useState('Hello World');

  const handleMethodToggle = (methodValue: string) => {
    if (selectedMethods.includes(methodValue)) {
      onMethodsChange(selectedMethods.filter(m => m !== methodValue));
    } else {
      onMethodsChange([...selectedMethods, methodValue]);
    }
  };

  const handleRemoveMethod = (methodValue: string) => {
    onMethodsChange(selectedMethods.filter(m => m !== methodValue));
  };

  const clearAllMethods = () => {
    onMethodsChange([]);
  };

  const getMethodsByCategory = () => {
    const categories: { [key: string]: EncodingMethod[] } = {};
    ENCODING_METHODS.forEach(method => {
      if (!categories[method.category]) {
        categories[method.category] = [];
      }
      categories[method.category].push(method);
    });
    return categories;
  };

  const getSelectedMethodInfo = (methodValue: string) => {
    return ENCODING_METHODS.find(m => m.value === methodValue);
  };

  const categories = getMethodsByCategory();

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Encoding Methods
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Select encoding methods to apply to prompts before testing. Multiple methods will be applied sequentially.
        </Typography>
        
        {selectedMethods.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Selected Methods ({selectedMethods.length}):
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {selectedMethods.map((methodValue, index) => {
                const methodInfo = getSelectedMethodInfo(methodValue);
                return (
                  <Chip
                    key={methodValue}
                    label={`${index + 1}. ${methodInfo?.label || methodValue}`}
                    onDelete={() => handleRemoveMethod(methodValue)}
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                );
              })}
            </Box>
            <Button
              size="small"
              onClick={clearAllMethods}
              sx={{ mt: 1 }}
              disabled={disabled}
            >
              Clear All
            </Button>
          </Box>
        )}
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Available Encoding Methods
        </Typography>
        
        {Object.entries(categories).map(([categoryName, methods]) => (
          <Box key={categoryName} sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              {categoryName} Encodings
            </Typography>
            <Grid container spacing={1}>
              {methods.map((method) => (
                <Grid item xs={12} sm={6} md={4} key={method.value}>
                  <Box
                    sx={{
                      p: 1,
                      border: selectedMethods.includes(method.value) ? '2px solid' : '1px solid',
                      borderColor: selectedMethods.includes(method.value) ? 'primary.main' : 'divider',
                      borderRadius: 1,
                      cursor: disabled ? 'default' : 'pointer',
                      backgroundColor: selectedMethods.includes(method.value) ? 'primary.50' : 'background.paper',
                      position: 'relative',
                      '&:hover': disabled ? {} : {
                        backgroundColor: selectedMethods.includes(method.value) ? 'primary.100' : 'action.hover'
                      }
                    }}
                    onClick={() => !disabled && handleMethodToggle(method.value)}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="body2" fontWeight="medium">
                        {method.label}
                      </Typography>
                      <Tooltip title={method.description}>
                        <InfoIcon 
                          sx={{ 
                            fontSize: '14px',
                            position: 'absolute',
                            top: 4,
                            right: 4
                          }} 
                          color="action" 
                        />
                      </Tooltip>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
            <Divider sx={{ mt: 2 }} />
          </Box>
        ))}
      </Paper>

      <Box sx={{ mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<InfoIcon />}
          onClick={() => setShowPreview(!showPreview)}
          size="small"
        >
          {showPreview ? 'Hide' : 'Show'} Encoding Preview
        </Button>
        
        {showPreview && (
          <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Encoding Preview
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Test text:
              </Typography>
              <Box
                component="input"
                value={previewText}
                onChange={(e) => setPreviewText(e.target.value)}
                sx={{
                  width: '100%',
                  p: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  fontFamily: 'monospace'
                }}
              />
            </Box>
            
            {selectedMethods.length > 0 ? (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Encoding chain: {selectedMethods.map(m => getSelectedMethodInfo(m)?.label).join(' → ')}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Note: Preview functionality requires backend integration
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Select encoding methods to see preview
              </Typography>
            )}
          </Paper>
        )}
      </Box>
    </Box>
  );
};

export default EncodingSelector;
