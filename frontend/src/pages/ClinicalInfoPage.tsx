import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  InputAdornment,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

import { MasterItemSummary } from '../types/patient';

const priceFormatter = new Intl.NumberFormat('ko-KR');

const ClinicalInfoPage = () => {
  const [items, setItems] = useState<MasterItemSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          category: 'ACT',
          page_size: '100'
        });
        const response = await fetch(`/api/master/items/?${params.toString()}`, {
          signal: controller.signal,
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error();
        }
        const payload = await response.json();
        if (!active) {
          return;
        }
        setItems(Array.isArray(payload.results) ? payload.results : []);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError('수가 마스터 데이터를 불러오지 못했습니다.');
          setItems([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const filteredItems = useMemo(() => {
    if (!search.trim()) {
      return items;
    }
    const keyword = search.trim().toLowerCase();
    return items.filter(
      (item) =>
        item.code.toLowerCase().includes(keyword) ||
        item.name.toLowerCase().includes(keyword)
    );
  }, [items, search]);

  return (
    <Stack spacing={4}>
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          임상정보
        </Typography>
        <Typography color="text.secondary">
          수술·처치·기타처방 항목에 필요한 수가 데이터를 확인할 수 있습니다.
        </Typography>
      </Box>

      <Card sx={{ borderRadius: 3, boxShadow: 'none', border: '1px solid #e2e8f0' }}>
        <CardContent>
          <Stack spacing={3}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="space-between">
              <Box>
                <Typography variant="h6" fontWeight={700}>
                  수술·처치·기타처방
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  건강보험심사평가원 한방 수가 예시 파일을 기준으로 임포트된 데이터를 제공합니다.
                </Typography>
              </Box>
              <TextField
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="수가코드 또는 한글명을 검색하세요"
                size="small"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
                sx={{ width: { xs: '100%', sm: 320 } }}
              />
            </Stack>

            {error ? <Alert severity="error">{error}</Alert> : null}

            <Box sx={{ position: 'relative', minHeight: loading ? 200 : undefined }}>
              {loading ? (
                <Stack
                  alignItems="center"
                  justifyContent="center"
                  spacing={2}
                  sx={{ minHeight: 200 }}
                >
                  <CircularProgress />
                  <Typography color="text.secondary">데이터를 불러오는 중입니다…</Typography>
                </Stack>
              ) : (
                <Box sx={{ overflowX: 'auto' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>수가코드</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>한글명</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>한방병의원단가</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredItems.length ? (
                        filteredItems.map((item) => (
                          <TableRow key={item.id} hover>
                            <TableCell sx={{ fontFamily: 'monospace' }}>{item.code}</TableCell>
                            <TableCell>{item.name}</TableCell>
                            <TableCell>
                              {typeof item.price === 'number'
                                ? `₩${priceFormatter.format(item.price)}`
                                : '정보 없음'}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={3} align="center" sx={{ py: 6 }}>
                            <Typography color="text.secondary">
                              {search.trim()
                                ? '검색어와 일치하는 수가 항목이 없습니다.'
                                : '등록된 수가 항목이 없습니다.'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </Box>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
};

export default ClinicalInfoPage;

