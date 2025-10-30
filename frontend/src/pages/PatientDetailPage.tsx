import { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useNavigate, useParams } from 'react-router-dom';
import { usePatientContext } from '../context/PatientContext';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import NoteAddIcon from '@mui/icons-material/NoteAdd';
import MedicationIcon from '@mui/icons-material/Medication';

const defaultVitals = {
  bp: '128/80 mmHg',
  pulse: '78 bpm',
  temp: '36.7 ℃',
  resp: '18 bpm',
  height: '168 cm',
  weight: '62 kg',
  bmi: '21.9 kg/m²'
};

const defaultLabs = [
  { name: 'CBC', value: '정상', date: '2025-09-20' },
  { name: '간기능', value: '정상', date: '2025-09-01' },
  { name: 'HbA1c', value: '6.2%', date: '2025-08-15' }
];

const availableSlots = ['09:30', '10:00', '10:30', '11:00', '13:30', '14:00'];

const PatientDetailPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { getPatient } = usePatientContext();
  const patient = patientId ? getPatient(patientId) : undefined;

  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [newMedication, setNewMedication] = useState('Acetaminophen 500mg');
  const [diagnosis, setDiagnosis] = useState('KCD 코드 또는 병명');
  const [notes, setNotes] = useState('의무기록을 자유 형식으로 입력하세요');
  const [showSaved, setShowSaved] = useState(false);

  const formattedDate = useMemo(
    () => format(selectedDate, 'PPP (EEE)', { locale: ko }),
    [selectedDate]
  );

  const isoDate = useMemo(() => format(selectedDate, 'yyyy-MM-dd'), [selectedDate]);

  if (!patient) {
    return (
      <Stack spacing={2}>
        <Button variant="text" onClick={() => navigate('/patients')}>
          ← 환자 목록으로 돌아가기
        </Button>
        <Alert severity="warning">요청하신 환자 정보를 찾을 수 없습니다.</Alert>
      </Stack>
    );
  }

  const confirmOrder = () => {
    setShowSaved(true);
    setTimeout(() => setShowSaved(false), 3000);
  };

  return (
    <Stack spacing={4}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <div>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {patient.name} 환자 차트
          </Typography>
          <Typography color="text.secondary">
            주민등록번호 {patient.registrationNumber} · 연락처 {patient.phone}
          </Typography>
        </div>
        <Button variant="outlined" onClick={() => navigate('/patients')}>
          환자 목록으로
        </Button>
      </Stack>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  환자정보
                </Typography>
                <Stack spacing={1.5}>
                  <InfoRow label="생년월일" value={patient.birthDate} />
                  <InfoRow label="성별" value={patient.sex} />
                  <InfoRow label="연락처" value={patient.phone} />
                  <InfoRow label="등록번호" value={patient.registrationNumber} />
                  <InfoRow label="주치의" value={patient.primaryPhysician} />
                </Stack>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  활력징후 / 신체계측
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(defaultVitals).map(([key, value]) => (
                    <Grid key={key} item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        {key.toUpperCase()}
                      </Typography>
                      <Typography variant="h6" fontWeight={700}>
                        {value}
                      </Typography>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  검사결과
                </Typography>
                <List dense>
                  {defaultLabs.map((lab) => (
                    <ListItem key={lab.name} disablePadding sx={{ mb: 1 }}>
                      <ListItemText
                        primary={lab.name}
                        secondary={`${lab.value} · ${format(new Date(lab.date), 'yyyy-MM-dd')}`}
                      />
                    </ListItem>
                  ))}
                </List>
                <Button fullWidth variant="outlined">
                  조회하기
                </Button>
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        <Grid item xs={12} md={5}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    진료 날짜 선택
                  </Typography>
                  <IconButton color="primary">
                    <CalendarMonthIcon />
                  </IconButton>
                </Stack>
                <Typography variant="h5" fontWeight={700} gutterBottom>
                  {formattedDate}
                </Typography>
                <TextField
                  type="date"
                  value={isoDate}
                  onChange={(event) => {
                    const next = event.target.value ? new Date(event.target.value) : new Date();
                    setSelectedDate(next);
                  }}
                  InputLabelProps={{ shrink: true }}
                  sx={{ mb: 2, width: '60%' }}
                />
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {availableSlots.map((slot) => (
                    <Button
                      key={slot}
                      variant="contained"
                      color="inherit"
                      sx={{
                        backgroundColor: '#eef2ff',
                        color: '#312e81',
                        '&:hover': { backgroundColor: '#e0e7ff' }
                      }}
                    >
                      {slot}
                    </Button>
                  ))}
                </Box>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <NoteAddIcon color="primary" />
                  <Typography variant="subtitle2" color="text.secondary">
                    의무기록
                  </Typography>
                </Stack>
                <TextField
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  multiline
                  minRows={5}
                  fullWidth
                  placeholder="의무기록을 입력하세요"
                />
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        <Grid item xs={12} md={3}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                  <MedicationIcon color="primary" />
                  <Typography variant="subtitle2" color="text.secondary">
                    처방 입력
                  </Typography>
                </Stack>
                <TextField
                  label="약물"
                  fullWidth
                  value={newMedication}
                  onChange={(event) => setNewMedication(event.target.value)}
                />
                <Button variant="contained" fullWidth sx={{ mt: 2 }} onClick={confirmOrder}>
                  처방전 생성
                </Button>
                {showSaved && (
                  <Alert sx={{ mt: 2 }} severity="success">
                    처방이 임시저장되었습니다.
                  </Alert>
                )}
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  진단
                </Typography>
                <TextField
                  label="KCD 코드 또는 병명"
                  value={diagnosis}
                  onChange={(event) => setDiagnosis(event.target.value)}
                  fullWidth
                />
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Stack>
  );
};

interface InfoRowProps {
  label: string;
  value: string;
}

const InfoRow = ({ label, value }: InfoRowProps) => (
  <Box>
    <Typography variant="body2" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="subtitle1" fontWeight={600}>
      {value}
    </Typography>
    <Divider sx={{ mt: 1 }} />
  </Box>
);

export default PatientDetailPage;
