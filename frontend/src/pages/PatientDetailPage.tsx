import { useMemo } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography
} from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useNavigate, useParams } from 'react-router-dom';
import usePatientDetail from '../hooks/usePatientDetail';
import { usePatientContext } from '../context/PatientContext';
import {
  AnthropometricsSnapshot,
  ClinicalNoteSummary,
  DiagnosisSummary,
  PatientSummary,
  PrescriptionSummary,
  VitalSnapshot
} from '../types/patient';

const formatDate = (value?: string | null) => {
  if (!value) {
    return '-';
  }
  try {
    return format(new Date(value), 'PPP', { locale: ko });
  } catch (err) {
    return value;
  }
};

const formatGender = (gender: PatientSummary['gender']) => {
  switch (gender) {
    case 'M':
      return '남';
    case 'F':
      return '여';
    default:
      return '기타';
  }
};

const PatientDetailPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const numericId = patientId ? Number(patientId) : null;
  const { findPatient } = usePatientContext();
  const { detail, loading, error } = usePatientDetail(numericId);

  const fallbackPatient = numericId ? findPatient(numericId) : undefined;
  const patient = detail?.patient ?? fallbackPatient;

  const latestVitals = detail?.latestVitals ?? null;
  const latestAnthro = detail?.latestAnthropometrics ?? null;

  const mergedDiagnoses = useMemo<DiagnosisSummary[]>(() => {
    if (!detail) {
      return [];
    }
    return detail.notes.flatMap((note) => note.diagnoses);
  }, [detail]);

  const mergedPrescriptions = useMemo<PrescriptionSummary[]>(() => {
    if (!detail) {
      return [];
    }
    return detail.notes.flatMap((note) => note.prescriptions);
  }, [detail]);

  const latestNote = detail?.notes[0];

  if (loading && !patient) {
    return (
      <Stack spacing={3} alignItems="center" justifyContent="center" sx={{ minHeight: '60vh' }}>
        <CircularProgress />
        <Typography color="text.secondary">환자 정보를 불러오는 중입니다…</Typography>
      </Stack>
    );
  }

  if (!patient) {
    return (
      <Stack spacing={2}>
        <Alert severity="warning">요청하신 환자 정보를 찾을 수 없습니다.</Alert>
      </Stack>
    );
  }

  return (
    <Stack spacing={4}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <div>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {patient.name} 환자 차트
          </Typography>
          <Typography color="text.secondary">
            등록번호 {patient.regNo} · 주민등록번호 {patient.rrn}
          </Typography>
        </div>
        <Typography
          variant="body2"
          sx={{ cursor: 'pointer' }}
          color="primary"
          onClick={() => navigate('/patients')}
        >
          ← 환자 목록으로 돌아가기
        </Typography>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}

      <Grid container spacing={3} alignItems="stretch">
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  환자정보
                </Typography>
                <Stack spacing={1.5}>
                  <InfoRow label="생년월일" value={formatDate(patient.birthDate)} />
                  <InfoRow label="나이" value={`${patient.age}세`} />
                  <InfoRow label="성별" value={formatGender(patient.gender)} />
                  <InfoRow label="연락처" value={patient.phone || '-'} />
                  <InfoRow label="주소" value={patient.address || '-'} />
                  <InfoRow label="등록일" value={formatDate(patient.createdAt)} />
                </Stack>
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  최신 활력징후
                </Typography>
                {latestVitals ? (
                  <VitalsGrid vitals={latestVitals} anthropometrics={latestAnthro} />
                ) : (
                  <Typography color="text.secondary">활력징후 기록이 없습니다.</Typography>
                )}
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  외부 문서
                </Typography>
                {detail?.documents?.length ? (
                  <List dense>
                    {detail.documents.map((doc) => (
                      <ListItem key={doc.id} disablePadding sx={{ mb: 1 }}>
                        <ListItemText
                          primary={doc.title}
                          secondary={`${doc.source || '미상'} · ${formatDate(doc.recordedAt)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">외부 문서가 없습니다.</Typography>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        <Grid item xs={12} md={5}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  최근 진료기록
                </Typography>
                {detail?.notes?.length ? (
                  <Stack spacing={3}>
                    {detail.notes.map((note) => (
                      <ClinicalNoteCard key={note.id} note={note} />
                    ))}
                  </Stack>
                ) : (
                  <Typography color="text.secondary">임상 노트가 없습니다.</Typography>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>

        <Grid item xs={12} md={3}>
          <Stack spacing={3}>
            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  최근 처방
                </Typography>
                {mergedPrescriptions.length ? (
                  <List dense>
                    {mergedPrescriptions.map((item) => (
                      <ListItem key={`${item.id}-${item.name}`} disablePadding sx={{ mb: 1 }}>
                        <ListItemText
                          primary={item.name}
                          secondary={[item.dose, item.freq, item.days ? `${item.days}일` : '']
                            .filter(Boolean)
                            .join(' · ')}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary">처방 내역이 없습니다.</Typography>
                )}
              </CardContent>
            </Card>

            <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  진단
                </Typography>
                {mergedDiagnoses.length ? (
                  <Stack spacing={1}>
                    {mergedDiagnoses.map((diagnosis) => (
                      <Chip
                        key={`${diagnosis.id}-${diagnosis.code}`}
                        label={`${diagnosis.code} · ${diagnosis.name}`}
                        sx={{ justifyContent: 'flex-start' }}
                      />
                    ))}
                  </Stack>
                ) : (
                  <Typography color="text.secondary">진단 기록이 없습니다.</Typography>
                )}
              </CardContent>
            </Card>

            {latestNote?.allergies?.length ? (
              <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    알레르기
                  </Typography>
                  <List dense>
                    {latestNote.allergies.map((allergy) => (
                      <ListItem key={allergy.id} disablePadding sx={{ mb: 1 }}>
                        <ListItemText
                          primary={allergy.substance}
                          secondary={[allergy.reaction, allergy.severity].filter(Boolean).join(' · ')}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            ) : null}
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

const VitalsGrid = ({
  vitals,
  anthropometrics
}: {
  vitals: VitalSnapshot;
  anthropometrics: AnthropometricsSnapshot | null;
}) => {
  const metrics: { label: string; value: string }[] = [
    { label: '혈압', value: vitals.systolic && vitals.diastolic ? `${vitals.systolic}/${vitals.diastolic} mmHg` : '-' },
    { label: '심박수', value: vitals.heartRate ? `${vitals.heartRate} bpm` : '-' },
    { label: '호흡수', value: vitals.respRate ? `${vitals.respRate} /min` : '-' },
    { label: '체온', value: vitals.temperatureC ? `${vitals.temperatureC.toFixed(1)} ℃` : '-' },
    { label: '산소포화도', value: vitals.spo2 ? `${vitals.spo2}%` : '-' },
    { label: '통증점수', value: vitals.painScore ? `${vitals.painScore}` : '-' },
    {
      label: '신장',
      value: anthropometrics?.heightCm ? `${anthropometrics.heightCm.toFixed(1)} cm` : '-'
    },
    {
      label: '체중',
      value: anthropometrics?.weightKg ? `${anthropometrics.weightKg.toFixed(1)} kg` : '-'
    },
    { label: 'BMI', value: anthropometrics?.bmi ? anthropometrics.bmi.toFixed(1) : '-' }
  ];

  return (
    <Grid container spacing={2}>
      {metrics.map((metric) => (
        <Grid item xs={6} key={metric.label}>
          <Typography variant="body2" color="text.secondary">
            {metric.label}
          </Typography>
          <Typography variant="h6" fontWeight={700}>
            {metric.value}
          </Typography>
        </Grid>
      ))}
    </Grid>
  );
};

const ClinicalNoteCard = ({ note }: { note: ClinicalNoteSummary }) => (
  <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 2, p: 2 }}>
    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
      {formatDate(note.visitDate)} · {note.chiefComplaint || '주증상 미입력'}
    </Typography>
    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }} gutterBottom>
      {note.subjective || 'S 미입력'}
    </Typography>
    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }} gutterBottom>
      {note.objective || 'O 미입력'}
    </Typography>
    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }} gutterBottom>
      {note.assessment || 'A 미입력'}
    </Typography>
    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
      {note.plan || 'P 미입력'}
    </Typography>
  </Box>
);

export default PatientDetailPage;
