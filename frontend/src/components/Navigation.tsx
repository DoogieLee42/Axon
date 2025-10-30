import { Box, List, ListItemButton, ListItemText, Typography } from '@mui/material';
import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <Box
      component="nav"
      sx={{
        width: 260,
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e2e8f0',
        p: 3,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Typography variant="h5" fontWeight={700} mb={4}>
        Axon EMR
      </Typography>
      <List sx={{ flexGrow: 1 }}>
        <ListItemButton
          component={NavLink}
          to="/patients"
          sx={{
            borderRadius: 2,
            mb: 1,
            '&.active': {
              backgroundColor: '#eef2ff'
            }
          }}
        >
          <ListItemText primary="환자 목록" secondary="등록 및 관리" />
        </ListItemButton>
      </List>
      <Typography variant="caption" color="text.secondary">
        © {new Date().getFullYear()} Axon Medical Records
      </Typography>
    </Box>
  );
};

export default Navigation;
