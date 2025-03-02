import { useState } from 'react';
import {
    Box, Button, Paper, Typography,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%' alignItems='center'>
                <Paper 
                    elevation={3} 
                    sx={{ 
                        mt: 2, 
                        width: '500px', 
                        padding: 2, 
                        border: '1px solid #1976d2',
                        backgroundColor: '#f0f8ff'
                    }}
                >
                    <Typography 
                        variant="body1" 
                        color="primary" 
                        sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                    >
                        {loadedData ? JSON.stringify(loadedData, null, 2) : "No Data Loaded"}
                    </Typography>
                </Paper>
                <Button onClick={handleLoad} sx={{ mt: 2 }} variant='contained'>
                    Load Data
                </Button>
                <Button onClick={() => setLoadedData(null)} sx={{ mt: 1 }} variant='contained' color='secondary'>
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
