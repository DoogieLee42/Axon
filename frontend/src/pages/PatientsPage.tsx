import { FormEvent, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  MenuItem,
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
import { Patient } from '../types/patient';

const emptyForm: Omit<Patient, 'id'> = {
  name: '',
  birthDate: '',
  sex: '남',
  phone: '',
  registrationNumber: '',
  primaryPhysician: ''
};

const PatientsPage = () => {
  const { patients, registerPatient } = usePatients();
  const [form, setForm] = useState(emptyForm);
  const navigate = useNavigate();

  const totalPatients = useMemo(() => patients.length, [patients]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    registerPatient(form);
    setForm(emptyForm);
  };

  return (
    <Stack spacing={4}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <div>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            환자 관리
          </Typography>
          <Typography color="text.secondary">등록된 모든 환자를 조회하고 신규 환자를 등록합니다.</Typography>
        </div>
        <Card sx={{ minWidth: 220, borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
          <CardContent>
            <Typography color="text.secondary" variant="body2">
              전체 환자 수
            </Typography>
            <Typography variant="h3" fontWeight={700}>
              {totalPatients}
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
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
                    <TableCell>주치의</TableCell>
                    <TableCell align="right">상세</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {patients.map((patient) => (
                    <TableRow key={patient.id} hover>
                      <TableCell>{patient.name}</TableCell>
                      <TableCell>{patient.birthDate}</TableCell>
                      <TableCell>{patient.sex}</TableCell>
                      <TableCell>{patient.primaryPhysician}</TableCell>
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
                  label="생년월일"
                  type="date"
                  value={form.birthDate}
                  onChange={(event) => setForm({ ...form, birthDate: event.target.value })}
                  InputLabelProps={{ shrink: true }}
                  required
                />
                <TextField
                  label="성별"
                  select
                  value={form.sex}
                  onChange={(event) => setForm({ ...form, sex: event.target.value as '남' | '여' })}
                >
                  <MenuItem value="남">남</MenuItem>
                  <MenuItem value="여">여</MenuItem>
                </TextField>
                <TextField
                  label="연락처"
                  value={form.phone}
                  onChange={(event) => setForm({ ...form, phone: event.target.value })}
                />
                <TextField
                  label="등록번호"
                  value={form.registrationNumber}
                  onChange={(event) => setForm({ ...form, registrationNumber: event.target.value })}
                />
                <TextField
                  label="주치의"
                  value={form.primaryPhysician}
                  onChange={(event) => setForm({ ...form, primaryPhysician: event.target.value })}
                />
                <Box textAlign="right">
                  <Button type="submit" variant="contained" size="large">
                    환자 등록
                  </Button>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  );
};

export default PatientsPage;
