import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Box } from '@mui/material';
import Navigation from './components/Navigation';
import PatientsPage from './pages/PatientsPage';
import PatientDetailPage from './pages/PatientDetailPage';
import ClinicalInfoPage from './pages/ClinicalInfoPage';
import { PatientProvider } from './context/PatientContext';

const App = () => {
  return (
    <PatientProvider>
      <BrowserRouter>
        <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
          <Navigation />
          <Box component="main" sx={{ flexGrow: 1, p: 4 }}>
            <Routes>
              <Route path="/patients" element={<PatientsPage />} />
              <Route path="/patients/:patientId" element={<PatientDetailPage />} />
              <Route path="/clinical-info" element={<ClinicalInfoPage />} />
              <Route path="*" element={<Navigate to="/patients" replace />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </PatientProvider>
  );
};

export default App;
