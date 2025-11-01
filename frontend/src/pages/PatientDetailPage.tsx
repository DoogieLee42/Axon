import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Typography
} from '@mui/material';
import AssignmentIndOutlinedIcon from '@mui/icons-material/AssignmentIndOutlined';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import MedicationLiquidOutlinedIcon from '@mui/icons-material/MedicationLiquidOutlined';
import VaccinesOutlinedIcon from '@mui/icons-material/VaccinesOutlined';
import CorporateFareOutlinedIcon from '@mui/icons-material/CorporateFareOutlined';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import HistoryEduOutlinedIcon from '@mui/icons-material/HistoryEduOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useNavigate, useParams } from 'react-router-dom';
import usePatientDetail from '../hooks/usePatientDetail';
import NoteComposer from '../components/NoteComposer';
import { usePatientContext } from '../context/PatientContext';
import { ClinicalNoteSummary, PatientSummary, PrescriptionSummary } from '../types/patient';

const cardStyles = {
  borderRadius: 3,
  boxShadow: '0 18px 36px rgba(15, 23, 42, 0.08)',
  border: '1px solid #e2e8f0',
  background: '#ffffff'
} as const;

const pillStyles = {
  borderRadius: 2,
  border: '1px solid #e2e8f0',
  padding: '12px 16px',
  backgroundColor: '#f8fafc'
} as const;

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

const formatDateTime = (value?: string | null) => {
  if (!value) {
    return '-';
  }
  try {
    return format(new Date(value), 'PPP p', { locale: ko });
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

interface SectionCardProps {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}

const SectionCard = ({ icon, title, subtitle, action, children }: SectionCardProps) => (
  <Card sx={cardStyles}>
    <CardContent sx={{ p: 3 }}>
      <Stack spacing={2.5}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 2,
                backgroundColor: '#eef2ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#4f46e5'
              }}
            >
              {icon}
            </Box>
            <Box>
              <Typography variant="subtitle1" fontWeight={700}>
                {title}
              </Typography>
              {subtitle ? (
                <Typography variant="body2" color="text.secondary">
                  {subtitle}
                </Typography>
              ) : null}
            </Box>
          </Stack>
          {action}
        </Stack>
        {children}
      </Stack>
    </CardContent>
  </Card>
);

interface MetricItem {
  label: string;
  value: string;
}

const MetricGrid = ({ metrics }: { metrics: MetricItem[] }) => (
  <Box
    sx={{
      display: 'grid',
      gap: 1.5,
      gridTemplateColumns: { xs: 'repeat(2, minmax(0, 1fr))', sm: 'repeat(3, minmax(0, 1fr))' }
    }}
  >
    {metrics.map((metric) => (
      <Box key={metric.label} sx={pillStyles}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          {metric.label}
        </Typography>
        <Typography variant="subtitle2" fontWeight={700}>
          {metric.value}
        </Typography>
      </Box>
    ))}
  </Box>
);

const LabeledValue = ({ label, value }: { label: string; value: string }) => (
  <Box>
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
      {label}
    </Typography>
    <Typography variant="body1" fontWeight={600}>
      {value}
    </Typography>
  </Box>
);

const PatientDetailPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const numericId = patientId ? Number(patientId) : null;
  const { findPatient } = usePatientContext();
  const { detail, loading, error, reload } = usePatientDetail(numericId);

  const fallbackPatient = numericId ? findPatient(numericId) : undefined;
  const patient = detail?.patient ?? fallbackPatient;

  const latestVitals = detail?.latestVitals ?? null;
  const latestAnthro = detail?.latestAnthropometrics ?? null;
  const labResults = detail?.labResults ?? [];
  const documents = detail?.documents ?? [];

  const latestNote = detail?.notes[0];

  const recentNotes = detail?.notes ?? [];

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

  const medicationItems = latestNote?.medications ?? [];
  const allergyItems = latestNote?.allergies ?? [];
  const prescriptionItems = latestNote?.prescriptions ?? [];

  const basicInfo = [
    { label: '생년월일', value: formatDate(patient.birthDate) },
    { label: '나이', value: `${patient.age}세` },
    { label: '성별', value: formatGender(patient.gender) },
    { label: '연락처', value: patient.phone || '-' },
    { label: '주소', value: patient.address || '-' },
    { label: '등록일', value: formatDate(patient.createdAt) },
    { label: '등록번호', value: patient.regNo },
    { label: '주민등록번호', value: patient.rrn }
  ];

  const vitalMetrics: MetricItem[] = [
    {
      label: '혈압',
      value:
        latestVitals?.systolic && latestVitals.diastolic
          ? `${latestVitals.systolic}/${latestVitals.diastolic} mmHg`
          : '-'
    },
    {
      label: '심박수',
      value: latestVitals?.heartRate ? `${latestVitals.heartRate} bpm` : '-'
    },
    {
      label: '호흡수',
      value: latestVitals?.respRate ? `${latestVitals.respRate} /min` : '-'
    },
    {
      label: '체온',
      value: latestVitals?.temperatureC ? `${latestVitals.temperatureC.toFixed(1)} ℃` : '-'
    },
    {
      label: '산소포화도',
      value: latestVitals?.spo2 ? `${latestVitals.spo2}%` : '-'
    },
    {
      label: '통증점수',
      value: latestVitals?.painScore ? `${latestVitals.painScore}` : '-'
    },
    {
      label: '신장',
      value: latestAnthro?.heightCm ? `${latestAnthro.heightCm.toFixed(1)} cm` : '-'
    },
    {
      label: '체중',
      value: latestAnthro?.weightKg ? `${latestAnthro.weightKg.toFixed(1)} kg` : '-'
    },
    {
      label: 'BMI',
      value: latestAnthro?.bmi ? latestAnthro.bmi.toFixed(1) : '-'
    }
  ];

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

      <Box
        sx={{
          display: 'grid',
          gap: 3,
          alignItems: 'start',
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'minmax(280px, 1fr) minmax(0, 2fr)',
            xl: '320px minmax(0, 1.2fr) minmax(340px, 0.9fr)'
          }
        }}
      >
        <Stack
          spacing={3}
          sx={{
            gridColumn: { xs: '1 / -1', lg: '1 / span 1' }
          }}
        >
          <SectionCard icon={<AssignmentIndOutlinedIcon />} title="환자정보" subtitle="기본 등록 정보">
            <Box
              sx={{
                display: 'grid',
                gap: 1.5,
                gridTemplateColumns: 'repeat(2, minmax(0, 1fr))'
              }}
            >
              {basicInfo.map((item) => (
                <LabeledValue key={item.label} label={item.label} value={item.value} />
              ))}
            </Box>
          </SectionCard>

          <SectionCard icon={<MonitorHeartIcon />} title="활력징후 / 신체계측">
            <MetricGrid metrics={vitalMetrics} />
          </SectionCard>

          <SectionCard
            icon={<MedicationLiquidOutlinedIcon />}
            title="약물정보"
            subtitle="최근 임상 기록 기준"
            action={
              prescriptionItems.length ? (
                <Button
                  variant="outlined"
                  size="small"
                  endIcon={<OpenInNewIcon fontSize="small" />}
                  onClick={() => navigate('/orders')}
                >
                  처방 내역
                </Button>
              ) : null
            }
          >
            {medicationItems.length ? (
              <Stack spacing={1.5}>
                {medicationItems.map((med) => (
                  <Box key={med.id} sx={pillStyles}>
                    <Typography variant="subtitle2" fontWeight={700}>
                      {med.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {[
                        med.code ? `코드 ${med.code}` : null,
                        med.dose ? `용량 ${med.dose}` : null,
                        med.freq ? `횟수 ${med.freq}` : null,
                        med.route ? `경로 ${med.route}` : null,
                        med.durationDays ? `${med.durationDays}일` : null
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">등록된 약물 정보가 없습니다.</Typography>
            )}
          </SectionCard>

          <SectionCard icon={<VaccinesOutlinedIcon />} title="약물 알레르기">
            {allergyItems.length ? (
              <Stack spacing={1.2}>
                {allergyItems.map((allergy) => (
                  <Box key={allergy.id} sx={pillStyles}>
                    <Typography variant="subtitle2" fontWeight={700}>
                      {allergy.substance}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {[allergy.reaction, allergy.severity].filter(Boolean).join(' · ') || '상세 정보 없음'}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">등록된 알레르기 정보가 없습니다.</Typography>
            )}
          </SectionCard>

          <SectionCard icon={<CorporateFareOutlinedIcon />} title="외부 의료기관 정보">
            {documents.length ? (
              <Stack spacing={1.5}>
                {documents.map((doc) => (
                  <Box key={doc.id} sx={pillStyles}>
                    <Typography variant="subtitle2" fontWeight={700}>
                      {doc.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {[doc.source || '기관 미상', formatDate(doc.recordedAt)].filter(Boolean).join(' · ')}
                    </Typography>
                    {doc.description ? (
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        {doc.description}
                      </Typography>
                    ) : null}
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">외부 의료기관 기록이 없습니다.</Typography>
            )}
          </SectionCard>

          <SectionCard
            icon={<ScienceOutlinedIcon />}
            title="검사 결과"
            subtitle="최근 등록 순"
          >
            {labResults.length ? (
              <Stack spacing={1.5}>
                {labResults.map((result) => (
                  <Box key={result.id} sx={pillStyles}>
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                      <Box>
                        <Typography variant="subtitle2" fontWeight={700}>
                          {result.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {[result.provider || '의료기관 미상', formatDate(result.recordedAt)]
                            .filter(Boolean)
                            .join(' · ')}
                        </Typography>
                      </Box>
                      {result.fileUrl ? (
                        <Button
                          href={result.fileUrl}
                          target="_blank"
                          rel="noreferrer"
                          variant="outlined"
                          size="small"
                          endIcon={<OpenInNewIcon fontSize="small" />}
                        >
                          보기
                        </Button>
                      ) : null}
                    </Stack>
                    {result.summary ? (
                      <Typography variant="body2" sx={{ mt: 0.75 }}>
                        {result.summary}
                      </Typography>
                    ) : null}
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography color="text.secondary">등록된 검사 결과가 없습니다.</Typography>
            )}
          </SectionCard>
        </Stack>

        <Box
          sx={{
            gridColumn: {
              xs: '1 / -1',
              lg: '2 / span 1',
              xl: '2 / span 2'
            },
            display: 'grid',
            gap: 3
          }}
        >
          {numericId ? <NoteComposer patientId={numericId} onCreated={reload} /> : null}

          <Card sx={cardStyles}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2 }}>
                <Box
                  sx={{
                    width: 38,
                    height: 38,
                    borderRadius: 2,
                    backgroundColor: '#eef2ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#4f46e5'
                  }}
                >
                  <HistoryEduOutlinedIcon fontSize="small" />
                </Box>
                <Box>
                  <Typography variant="subtitle1" fontWeight={700}>
                    최근 진료기록
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    저장된 임상 노트를 확인하세요.
                  </Typography>
                </Box>
              </Stack>
              {recentNotes.length ? (
                <Stack spacing={3}>
                  {recentNotes.map((note) => (
                    <ClinicalNoteCard key={note.id} note={note} prescriptions={note.prescriptions} />
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">임상 노트가 없습니다.</Typography>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Stack>
  );
};

const NoteSection = ({ label, value }: { label: string; value: string }) => (
  <Box sx={{ mt: 1.5 }}>
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
      {value}
    </Typography>
  </Box>
);

const ClinicalNoteCard = ({
  note,
  prescriptions
}: {
  note: ClinicalNoteSummary;
  prescriptions: PrescriptionSummary[];
}) => {
  const hasNarrative = Boolean(note.narrative);
  const hasLegacy = Boolean(note.subjective || note.objective || note.assessment || note.plan);
  const hasSocial = Boolean(note.socialHistory);
  const hasFamily = Boolean(note.familyHistory);
  const hasPrescriptions = prescriptions.length > 0;
  const hasAny = hasNarrative || hasLegacy || hasSocial || hasFamily || hasPrescriptions;

  return (
    <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 2.5, p: 2.5, backgroundColor: '#f8fafc' }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        {formatDate(note.visitDate)} · {note.chiefComplaint || '주증상 미입력'}
      </Typography>
      {note.narrative ? <NoteSection label="의무기록" value={note.narrative} /> : null}
      {note.subjective ? <NoteSection label="S" value={note.subjective} /> : null}
      {note.objective ? <NoteSection label="O" value={note.objective} /> : null}
      {note.assessment ? <NoteSection label="A" value={note.assessment} /> : null}
      {note.plan ? <NoteSection label="P" value={note.plan} /> : null}
      {note.socialHistory ? <NoteSection label="사회력" value={note.socialHistory} /> : null}
      {note.familyHistory ? <NoteSection label="가족력" value={note.familyHistory} /> : null}
      {hasPrescriptions ? (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            처방
          </Typography>
          <Stack spacing={1}>
            {prescriptions.map((item) => (
              <Box
                key={item.id}
                sx={{
                  borderRadius: 2,
                  border: '1px solid #e2e8f0',
                  p: 1.5,
                  backgroundColor: '#ffffff'
                }}
              >
                <Typography fontWeight={600}>
                  {item.name}
                  {item.code ? ` (${item.code})` : ''}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {[
                    item.itemType,
                    item.dose,
                    item.freq,
                    item.route,
                    item.days ? `${item.days}일` : '',
                    item.qty ? `${item.qty}${item.unit || ''}` : '',
                    item.notes
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>
      ) : null}
      {!hasAny ? (
        <Typography variant="body2" color="text.secondary">
          기록된 내용이 없습니다.
        </Typography>
      ) : null}
    </Box>
  );
};

export default PatientDetailPage;
