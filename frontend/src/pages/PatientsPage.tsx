import { FormEvent, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  MenuItem,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import usePatients from '../hooks/usePatients';
import { CreatePatientInput, GenderCode } from '../types/patient';

const defaultForm: CreatePatientInput = {
  name: '',
  gender: 'F',
  birthDate: '',
  rrn: '',
  phone: '',
  address: ''
};

const genderOptions: { label: string; value: GenderCode }[] = [
  { label: '여', value: 'F' },
  { label: '남', value: 'M' },
  { label: '기타', value: 'U' }
];

const formatGender = (gender: GenderCode) => {
  switch (gender) {
    case 'M':
      return '남';
    case 'F':
      return '여';
    default:
      return '기타';
  }
};

const PatientsPage = () => {
  const { patients, loading, error, registerPatient } = usePatients();
  const [form, setForm] = useState<CreatePatientInput>(defaultForm);
  const [submitting, setSubmitting] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const navigate = useNavigate();

  const totalPatients = useMemo(() => patients.length, [patients]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) {
      return;
    }

    setSubmitting(true);
    const created = await registerPatient(form);
    setSubmitting(false);

    if (created) {
      setForm(defaultForm);
      setOpenSnackbar(true);
    }
  };

  return (
    <Stack spacing={4}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <div>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            환자 관리
          </Typography>
          <Typography color="text.secondary">등록된 환자를 조회하고 신규 환자를 등록합니다.</Typography>
        </div>
        <Card sx={{ minWidth: 220, borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              전체 환자 수
            </Typography>
            <Typography variant="h3" fontWeight={700}>
              {loading ? '…' : totalPatients}
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}

      <Grid container spacing={3} alignItems="stretch">
        <Grid item xs={12} md={7}>
          <Card sx={{ height: '100%', borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>
                등록 환자 목록
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>환자명</TableCell>
                    <TableCell>생년월일</TableCell>
                    <TableCell>성별</TableCell>
                    <TableCell>연락처</TableCell>
                    <TableCell>등록번호</TableCell>
                    <TableCell align="right">상세</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        환자 정보를 불러오는 중입니다…
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading && patients.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        등록된 환자가 없습니다. 신규 환자를 등록해 보세요.
                      </TableCell>
                    </TableRow>
                  )}
                  {patients.map((patient) => (
                    <TableRow key={patient.id} hover>
                      <TableCell>{patient.name}</TableCell>
                      <TableCell>{patient.birthDate}</TableCell>
                      <TableCell>{formatGender(patient.gender)}</TableCell>
                      <TableCell>{patient.phone || '-'}</TableCell>
                      <TableCell>{patient.regNo}</TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => navigate(`/patients/${patient.id}`)}
                        >
                          차트 보기
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
            <CardContent component="form" onSubmit={onSubmit}>
              <Typography variant="h6" fontWeight={700} gutterBottom>
                신규 환자 등록
              </Typography>
              <Stack spacing={2}>
                <TextField
                  label="환자명"
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  required
                />
                <TextField
                  label="성별"
                  select
                  value={form.gender}
                  onChange={(event) => setForm({ ...form, gender: event.target.value as GenderCode })}
                >
                  {genderOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="생년월일"
                  type="date"
                  value={form.birthDate}
                  onChange={(event) => setForm({ ...form, birthDate: event.target.value })}
                  InputLabelProps={{ shrink: true }}
                  required
                />
                <TextField
                  label="주민등록번호"
                  value={form.rrn}
                  onChange={(event) => setForm({ ...form, rrn: event.target.value })}
                  placeholder="예: 900101-1234567"
                  required
                />
                <TextField
                  label="연락처"
                  value={form.phone}
                  onChange={(event) => setForm({ ...form, phone: event.target.value })}
                />
                <TextField
                  label="주소"
                  value={form.address}
                  onChange={(event) => setForm({ ...form, address: event.target.value })}
                />
                <Box textAlign="right">
                  <Button type="submit" variant="contained" size="large" disabled={submitting}>
                    {submitting ? '등록 중…' : '환자 등록'}
                  </Button>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        autoHideDuration={4000}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        open={openSnackbar}
        onClose={() => setOpenSnackbar(false)}
        message="환자 등록이 완료되었습니다."
      />
    </Stack>
  );
};

export default PatientsPage;
