import { FormEvent, SyntheticEvent, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Snackbar,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import CloseIcon from '@mui/icons-material/Close';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import dayjs, { Dayjs } from 'dayjs';

import { ClinicalNoteSummary, MasterItemSummary } from '../types/patient';
import { getCsrfToken } from '../utils/csrf';

type OrderType = 'DRUG' | 'TEST' | 'PROC' | 'FAVORITE' | 'BUNDLE';

interface DiagnosisDraft {
  code: string;
  name: string;
  source: string;
}

interface OrderDraft {
  id: string;
  itemType: OrderType;
  code: string;
  name: string;
  qty: string;
  unit: string;
  dose: string;
  freq: string;
  route: string;
  days: string;
  notes: string;
}

interface NoteComposerProps {
  patientId: number;
  onCreated?: (note: ClinicalNoteSummary) => void;
}

const ORDER_META: Record<
  OrderType,
  {
    label: string;
    masterCategory: string | null;
  }
> = {
  DRUG: { label: '약물', masterCategory: 'DRG' },
  TEST: { label: '검사', masterCategory: 'ACT' },
  PROC: { label: '수술·처치/기타', masterCategory: 'ACT' },
  FAVORITE: { label: '즐겨찾기', masterCategory: null },
  BUNDLE: { label: '묶음', masterCategory: null }
};

const createDraftId = () => Math.random().toString(36).slice(2, 10);

const composerCardSx = {
  borderRadius: 3,
  border: '1px solid #e2e8f0',
  boxShadow: '0 18px 36px rgba(15, 23, 42, 0.08)',
  backgroundColor: '#ffffff'
} as const;

const priceFormatter = new Intl.NumberFormat('ko-KR');

type OrderListState = {
  items: MasterItemSummary[];
  loading: boolean;
  loaded: boolean;
};

const createOrderListState = (): OrderListState => ({
  items: [],
  loading: false,
  loaded: false
});

const createInitialOrderLists = (): Record<OrderType, OrderListState> => ({
  DRUG: createOrderListState(),
  TEST: createOrderListState(),
  PROC: createOrderListState(),
  FAVORITE: createOrderListState(),
  BUNDLE: createOrderListState()
});

const NoteComposer = ({ patientId, onCreated }: NoteComposerProps) => {
  const [narrative, setNarrative] = useState('');
  const [socialHistory, setSocialHistory] = useState('');
  const [familyHistory, setFamilyHistory] = useState('');
  const [diagnosisQuery, setDiagnosisQuery] = useState('');
  const [diagnosisOptions, setDiagnosisOptions] = useState<MasterItemSummary[]>([]);
  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [selectedDiagnoses, setSelectedDiagnoses] = useState<DiagnosisDraft[]>([]);
  const [diagnosisList, setDiagnosisList] = useState<MasterItemSummary[]>([]);
  const [diagnosisListLoading, setDiagnosisListLoading] = useState(false);

  const [activeOrderType, setActiveOrderType] = useState<OrderType>('DRUG');
  const [orderQuery, setOrderQuery] = useState('');
  const [orderOptions, setOrderOptions] = useState<MasterItemSummary[]>([]);
  const [orderLoading, setOrderLoading] = useState(false);
  const [selectedOrders, setSelectedOrders] = useState<OrderDraft[]>([]);
  const [orderLists, setOrderLists] = useState<Record<OrderType, OrderListState>>(createInitialOrderLists);
  const orderListsRef = useRef(orderLists);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successOpen, setSuccessOpen] = useState(false);
  const [visitDate, setVisitDate] = useState<Dayjs | null>(dayjs());
  const [historyTab, setHistoryTab] = useState<'social' | 'family'>('social');

  useEffect(() => {
    if (diagnosisQuery.trim().length < 2) {
      setDiagnosisOptions([]);
      return;
    }

    let active = true;
    const controller = new AbortController();
    const handle = window.setTimeout(async () => {
      setDiagnosisLoading(true);
      try {
        const params = new URLSearchParams({
          category: 'DX',
          page_size: '20',
          search: diagnosisQuery.trim()
        });
        const response = await fetch(`/api/master/items/?${params.toString()}`, {
          signal: controller.signal,
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error();
        }
        const payload = await response.json();
        if (active) {
          setDiagnosisOptions(Array.isArray(payload.results) ? payload.results : []);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setDiagnosisOptions([]);
        }
      } finally {
        if (active) {
          setDiagnosisLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [diagnosisQuery]);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const loadInitialDiagnoses = async () => {
      setDiagnosisListLoading(true);
      try {
        const params = new URLSearchParams({
          category: 'DX',
          page_size: '50'
        });
        const response = await fetch(`/api/master/items/?${params.toString()}`, {
          signal: controller.signal,
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error();
        }
        const payload = await response.json();
        if (active) {
          setDiagnosisList(Array.isArray(payload.results) ? payload.results : []);
        }
      } catch (err) {
        if (!controller.signal.aborted && active) {
          setDiagnosisList([]);
        }
      } finally {
        if (active) {
          setDiagnosisListLoading(false);
        }
      }
    };

    loadInitialDiagnoses();

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const meta = ORDER_META[activeOrderType];
    if (!meta.masterCategory) {
      setOrderOptions([]);
      setOrderLoading(false);
      return;
    }

    if (orderQuery.trim().length < 2) {
      setOrderOptions([]);
      return;
    }

    let active = true;
    const controller = new AbortController();
    const handle = window.setTimeout(async () => {
      setOrderLoading(true);
      try {
        const params = new URLSearchParams({
          category: meta.masterCategory as string,
          page_size: '20',
          search: orderQuery.trim()
        });
        const response = await fetch(`/api/master/items/?${params.toString()}`, {
          signal: controller.signal,
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error();
        }
        const payload = await response.json();
        if (active) {
          setOrderOptions(Array.isArray(payload.results) ? payload.results : []);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setOrderOptions([]);
        }
      } finally {
        if (active) {
          setOrderLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [orderQuery, activeOrderType]);

  useEffect(() => {
    const fetchType = activeOrderType;
    const meta = ORDER_META[fetchType];
    const category = meta.masterCategory;
    if (!category) {
      return;
    }

    const currentState = orderListsRef.current[fetchType];
    if (currentState.loaded || currentState.loading) {
      return;
    }

    let active = true;
    const controller = new AbortController();

    setOrderLists((prev) => ({
      ...prev,
      [fetchType]: { ...prev[fetchType], loading: true }
    }));

    const loadOrderList = async () => {
      try {
        const params = new URLSearchParams({
          category,
          page_size: '50'
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
        const items = Array.isArray(payload.results) ? payload.results : [];
        setOrderLists((prev) => ({
          ...prev,
          [fetchType]: { items, loading: false, loaded: true }
        }));
      } catch (err) {
        if (!active) {
          return;
        }
        setOrderLists((prev) => ({
          ...prev,
          [fetchType]: { ...prev[fetchType], loading: false, loaded: true }
        }));
      }
    };

    loadOrderList();

    return () => {
      active = false;
      controller.abort();
      setOrderLists((prev) => ({
        ...prev,
        [fetchType]: { ...prev[fetchType], loading: false }
      }));
    };
  }, [activeOrderType]);

  const handleDiagnosisSelect = (_event: SyntheticEvent, value: MasterItemSummary | string | null) => {
    if (!value) {
      return;
    }
    let code = '';
    let name = '';
    let source = 'master';
    if (typeof value === 'string') {
      name = value.trim();
      code = name.slice(0, 32);
      source = 'manual';
    } else {
      code = value.code;
      name = value.name;
      source = 'master';
    }

    if (!name) {
      return;
    }
    setSelectedDiagnoses((prev) => {
      if (prev.some((diag) => diag.code === code && diag.name === name)) {
        return prev;
      }
      return [...prev, { code, name, source }];
    });
    setDiagnosisQuery('');
  };

  const handleDiagnosisRemove = (code: string, name: string) => {
    setSelectedDiagnoses((prev) => prev.filter((diag) => !(diag.code === code && diag.name === name)));
  };

  const appendOrderDraft = (itemType: OrderType, data: { code?: string; name?: string; unit?: string | null }) => {
    const code = (data.code || '').trim();
    const name = (data.name || '').trim();
    const unit = (data.unit || '').trim();
    if (!name) {
      return;
    }
    setSelectedOrders((prev) => {
      if (prev.some((order) => order.itemType === itemType && order.code === code && order.name === name)) {
        return prev;
      }
      const draft: OrderDraft = {
        id: createDraftId(),
        itemType,
        code,
        name,
        qty: '1',
        unit,
        dose: '',
        freq: '',
        route: '',
        days: '',
        notes: ''
      };
      return [...prev, draft];
    });
  };

  const handleDiagnosisQuickAdd = (item: MasterItemSummary) => {
    if (!item) {
      return;
    }
    const code = (item.code || '').trim();
    const name = (item.name || '').trim();
    if (!code || !name) {
      return;
    }
    setSelectedDiagnoses((prev) => {
      if (prev.some((diag) => diag.code === code && diag.name === name)) {
        return prev;
      }
      return [...prev, { code, name, source: 'master' }];
    });
  };

  const handleOrderSelect = (_event: SyntheticEvent, value: MasterItemSummary | string | null) => {
    if (!value) {
      return;
    }
    if (typeof value === 'string') {
      const name = value.trim();
      if (!name) {
        return;
      }
      appendOrderDraft(activeOrderType, { name });
    } else {
      appendOrderDraft(activeOrderType, { code: value.code, name: value.name, unit: value.unit });
    }
    setOrderQuery('');
  };

  const handleOrderChange = (id: string, field: keyof OrderDraft, value: string) => {
    setSelectedOrders((prev) =>
      prev.map((order) => (order.id === id ? { ...order, [field]: value } : order))
    );
  };

  const handleOrderRemove = (id: string) => {
    setSelectedOrders((prev) => prev.filter((order) => order.id !== id));
  };

  const handleOrderQuickAdd = (item: MasterItemSummary) => {
    if (!item) {
      return;
    }
    const name = (item.name || '').trim();
    if (!name) {
      return;
    }
    appendOrderDraft(activeOrderType, { code: item.code, name, unit: item.unit });
  };

  useEffect(() => {
    orderListsRef.current = orderLists;
  }, [orderLists]);

  const disableSubmit = useMemo(() => {
    return (
      !narrative.trim() &&
      !socialHistory.trim() &&
      !familyHistory.trim() &&
      selectedDiagnoses.length === 0 &&
      selectedOrders.length === 0
    );
  }, [narrative, socialHistory, familyHistory, selectedDiagnoses.length, selectedOrders.length]);

  const formatOrderPrimaryLabel = (item: MasterItemSummary) => {
    return [item.code, item.name].filter(Boolean).join(' · ');
  };

  const formatOrderSecondaryLabel = (item: MasterItemSummary) => {
    const details: string[] = [];
    if (item.unit) {
      details.push(`단위 ${item.unit}`);
    }
    if (typeof item.price === 'number') {
      details.push(`단가 ₩${priceFormatter.format(item.price)}`);
    }
    return details.join(' · ');
  };

  const formatOrderOptionLabel = (item: MasterItemSummary) => {
    const primary = formatOrderPrimaryLabel(item);
    const secondary = formatOrderSecondaryLabel(item);
    return secondary ? `${primary} · ${secondary}` : primary;
  };

  const currentOrderMeta = ORDER_META[activeOrderType];
  const currentOrderState = orderLists[activeOrderType];
  const currentOrderItems = currentOrderState.items;
  const currentOrderListLoading = currentOrderState.loading;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting || disableSubmit) {
      return;
    }
    setSubmitting(true);
    setError(null);

    const payload: Record<string, unknown> = {
      narrative,
      socialHistory,
      familyHistory,
      diagnoses: selectedDiagnoses.map((diag) => ({
        code: diag.code,
        name: diag.name,
        source: diag.source
      })),
      prescriptions: selectedOrders.map((order) => ({
        itemType: order.itemType,
        code: order.code,
        name: order.name,
        qty: order.qty,
        unit: order.unit,
        dose: order.dose,
        freq: order.freq,
        route: order.route,
        days: order.days,
        notes: order.notes
      }))
    };

    if (visitDate) {
      payload.visitDate = visitDate.toDate().toISOString();
    }

    try {
      const response = await fetch(`/api/patients/${patientId}/notes/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.ok === false) {
        throw new Error(data.error || '임상 기록 저장에 실패했습니다.');
      }
      const createdNote = data.note as ClinicalNoteSummary | undefined;
      setNarrative('');
      setSocialHistory('');
      setFamilyHistory('');
      setSelectedDiagnoses([]);
      setSelectedOrders([]);
      setVisitDate(dayjs());
      setSuccessOpen(true);
      if (createdNote && onCreated) {
        onCreated(createdNote);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          display: 'grid',
          gap: 3,
          alignItems: 'start',
          gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1fr) 360px' }
        }}
      >
        {error ? (
          <Alert severity="error" sx={{ gridColumn: '1 / -1' }}>
            {error}
          </Alert>
        ) : null}

        <Stack spacing={3} sx={{ gridColumn: { xs: '1 / -1', xl: '1 / 2' } }}>
          <Card sx={composerCardSx}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2.5}>
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={2}
                  justifyContent="space-between"
                  alignItems={{ xs: 'flex-start', sm: 'center' }}
                >
                  <Box>
                    <Typography variant="h6" fontWeight={700}>
                      의무기록
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      의무기록을 자유 형식으로 입력하세요 (S/O/A/P)
                    </Typography>
                  </Box>
                  <Box sx={{ width: { xs: '100%', sm: 220 } }}>
                    <DateTimePicker
                      label="기록 일시"
                      value={visitDate}
                      onChange={(value) => setVisitDate(value)}
                      format="YYYY-MM-DD HH:mm"
                      ampm={false}
                      slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                    />
                  </Box>
                </Stack>

                <TextField
                  label="의무기록"
                  multiline
                  minRows={8}
                  value={narrative}
                  onChange={(event) => setNarrative(event.target.value)}
                  placeholder="의무기록을 자유 형식으로 입력하세요 (S/O/A/P)"
                />
              </Stack>
            </CardContent>
          </Card>

          <Card sx={composerCardSx}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    사회력 / 가족력
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    흡연, 음주, 운동, 직업 등 사회력 기록을 남겨주세요.
                  </Typography>
                </Box>
                <Tabs
                  value={historyTab}
                  onChange={(_event, value) => setHistoryTab(value as 'social' | 'family')}
                  variant="scrollable"
                  allowScrollButtonsMobile
                >
                  <Tab label="사회력" value="social" />
                  <Tab label="가족력" value="family" />
                </Tabs>
                {historyTab === 'social' ? (
                  <TextField
                    label="사회력"
                    multiline
                    minRows={6}
                    value={socialHistory}
                    onChange={(event) => setSocialHistory(event.target.value)}
                    placeholder="흡연, 음주, 운동, 직업 등 사회력 기록"
                  />
                ) : (
                  <TextField
                    label="가족력"
                    multiline
                    minRows={6}
                    value={familyHistory}
                    onChange={(event) => setFamilyHistory(event.target.value)}
                    placeholder="가족 질환 이력 등을 입력하세요."
                  />
                )}
              </Stack>
            </CardContent>
          </Card>
        </Stack>

        <Stack spacing={3} sx={{ gridColumn: { xs: '1 / -1', xl: '2 / 3' } }}>
          <Card sx={composerCardSx}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    진단
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    KCD 코드 또는 명칭을 검색해 추가하세요.
                  </Typography>
                </Box>
                <Autocomplete
                  freeSolo
                  options={diagnosisOptions}
                  loading={diagnosisLoading}
                  value={null}
                  inputValue={diagnosisQuery}
                  onInputChange={(_event, value) => setDiagnosisQuery(value)}
                  onChange={handleDiagnosisSelect}
                  filterOptions={(options) => options}
                  getOptionLabel={(option) =>
                    typeof option === 'string' ? option : `${option.code} · ${option.name}`
                  }
                  renderOption={(props, option) => (
                    <li {...props} key={typeof option === 'string' ? option : option.code}>
                      {typeof option === 'string' ? option : `${option.code} · ${option.name}`}
                    </li>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="진단 검색 (2자 이상 입력)"
                      InputProps={{
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {diagnosisLoading ? <CircularProgress color="inherit" size={18} /> : null}
                            {params.InputProps.endAdornment}
                          </>
                        )
                      }}
                    />
                  )}
                />
                {selectedDiagnoses.length > 0 ? (
                  <Stack direction="row" flexWrap="wrap" gap={1}>
                    {selectedDiagnoses.map((diag) => (
                      <Chip
                        key={`${diag.code}-${diag.name}`}
                        label={`${diag.code || '미등록'} · ${diag.name}`}
                        onDelete={() => handleDiagnosisRemove(diag.code, diag.name)}
                      />
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    선택된 진단이 없습니다.
                  </Typography>
                )}

                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle2" color="text.secondary">
                      상병 코드 목록
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      전체 {diagnosisList.length}건 중 일부 예시
                    </Typography>
                  </Stack>
                  <Box
                    sx={{
                      maxHeight: 260,
                      overflowY: 'auto',
                      border: '1px solid #e2e8f0',
                      borderRadius: 2,
                      backgroundColor: '#f8fafc',
                      p: 1
                    }}
                  >
                    {diagnosisListLoading ? (
                      <Stack alignItems="center" justifyContent="center" spacing={1.5} sx={{ py: 4 }}>
                        <CircularProgress size={22} />
                        <Typography variant="body2" color="text.secondary">
                          상병 코드를 불러오는 중입니다…
                        </Typography>
                      </Stack>
                    ) : diagnosisList.length ? (
                      <Stack spacing={1}>
                        {diagnosisList.map((item) => (
                          <Button
                            key={item.id}
                            variant="text"
                            onClick={() => handleDiagnosisQuickAdd(item)}
                            sx={{
                              justifyContent: 'flex-start',
                              borderRadius: 2,
                              textTransform: 'none',
                              color: 'inherit',
                              backgroundColor: '#ffffff',
                              border: '1px solid #e2e8f0',
                              px: 1.5,
                              py: 1,
                              '&:hover': {
                                backgroundColor: '#e0e7ff'
                              }
                            }}
                            fullWidth
                          >
                            <Stack spacing={0.25} alignItems="flex-start">
                              <Typography fontWeight={700}>{item.code}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {item.name}
                              </Typography>
                            </Stack>
                          </Button>
                        ))}
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                        표시할 상병 코드가 없습니다.
                      </Typography>
                    )}
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          <Card sx={composerCardSx}>
            <CardContent sx={{ p: 3 }}>
              <Stack spacing={2.5}>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    처방 입력
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    약물, 검사, 처치/기타 처방을 추가하고 즐겨찾기/묶음을 관리하세요.
                  </Typography>
                </Box>
                <Tabs
                  value={activeOrderType}
                  onChange={(_event, value) => {
                    setActiveOrderType(value as OrderType);
                    setOrderQuery('');
                  }}
                  variant="scrollable"
                  allowScrollButtonsMobile
                >
                  <Tab label="약물" value="DRUG" />
                  <Tab label="검사" value="TEST" />
                  <Tab label="수술·처치/기타" value="PROC" />
                  <Tab label="즐겨찾기" value="FAVORITE" />
                  <Tab label="묶음" value="BUNDLE" />
                </Tabs>

                {currentOrderMeta.masterCategory ? (
                  <>
                    <Autocomplete
                      key={activeOrderType}
                      freeSolo
                      options={orderOptions}
                      loading={orderLoading}
                      value={null}
                      inputValue={orderQuery}
                      onInputChange={(_event, value) => setOrderQuery(value)}
                      onChange={handleOrderSelect}
                      filterOptions={(options) => options}
                      getOptionLabel={(option) =>
                        typeof option === 'string' ? option : formatOrderOptionLabel(option)
                      }
                      renderOption={(props, option) => {
                        if (typeof option === 'string') {
                          return (
                            <li {...props} key={option}>
                              {option}
                            </li>
                          );
                        }
                        const secondary = formatOrderSecondaryLabel(option);
                        return (
                          <li {...props} key={option.id}>
                            <Stack spacing={0.25} alignItems="flex-start">
                              <Typography fontWeight={600}>{formatOrderPrimaryLabel(option)}</Typography>
                              {secondary ? (
                                <Typography variant="caption" color="text.secondary">
                                  {secondary}
                                </Typography>
                              ) : null}
                            </Stack>
                          </li>
                        );
                      }}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label={`${ORDER_META[activeOrderType].label} 검색 (2자 이상 입력)`}
                          InputProps={{
                            ...params.InputProps,
                            endAdornment: (
                              <>
                                {orderLoading ? <CircularProgress color="inherit" size={18} /> : null}
                                {params.InputProps.endAdornment}
                              </>
                            )
                          }}
                        />
                      )}
                    />
                    <Stack spacing={1}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle2" color="text.secondary">
                          마스터 목록
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          총 {currentOrderItems.length}건
                        </Typography>
                      </Stack>
                      <Box
                        sx={{
                          maxHeight: 260,
                          overflowY: 'auto',
                          border: '1px solid #e2e8f0',
                          borderRadius: 2,
                          backgroundColor: '#f8fafc',
                          p: 1
                        }}
                      >
                        {currentOrderListLoading ? (
                          <Stack alignItems="center" justifyContent="center" spacing={1.5} sx={{ py: 4 }}>
                            <CircularProgress size={22} />
                            <Typography variant="body2" color="text.secondary">
                              항목을 불러오는 중입니다…
                            </Typography>
                          </Stack>
                        ) : currentOrderItems.length ? (
                          <Stack spacing={1}>
                            {currentOrderItems.map((item) => {
                              const secondary = formatOrderSecondaryLabel(item);
                              return (
                                <Button
                                  key={item.id}
                                  variant="text"
                                  onClick={() => handleOrderQuickAdd(item)}
                                  sx={{
                                    justifyContent: 'flex-start',
                                    borderRadius: 2,
                                    textTransform: 'none',
                                    color: 'inherit',
                                    backgroundColor: '#ffffff',
                                    border: '1px solid #e2e8f0',
                                    px: 1.5,
                                    py: 1,
                                    '&:hover': {
                                      backgroundColor: '#e0e7ff'
                                    }
                                  }}
                                  fullWidth
                                >
                                  <Stack spacing={0.25} alignItems="flex-start">
                                    <Typography fontWeight={700}>{formatOrderPrimaryLabel(item)}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {secondary || '상세 정보 없음'}
                                    </Typography>
                                  </Stack>
                                </Button>
                              );
                            })}
                          </Stack>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                            표시할 항목이 없습니다.
                          </Typography>
                        )}
                      </Box>
                    </Stack>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    즐겨찾기와 묶음 처방 기능은 준비 중입니다.
                  </Typography>
                )}

                <Stack spacing={2}>
                  {selectedOrders.length > 0 ? (
                    selectedOrders.map((order) => (
                      <Box
                        key={order.id}
                        sx={{
                          border: '1px solid #e2e8f0',
                          borderRadius: 2,
                          p: 2,
                          backgroundColor: '#f8fafc'
                        }}
                      >
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography fontWeight={600}>
                            {ORDER_META[order.itemType].label} · {order.name}
                          </Typography>
                          <IconButton size="small" onClick={() => handleOrderRemove(order.id)}>
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </Stack>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          코드: {order.code || '미등록'}
                        </Typography>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                          <TextField
                            label="용량/수량"
                            value={order.qty}
                            onChange={(event) => handleOrderChange(order.id, 'qty', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                          <TextField
                            label="단위"
                            value={order.unit}
                            onChange={(event) => handleOrderChange(order.id, 'unit', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                        </Stack>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 2 }}>
                          <TextField
                            label="1회 용량"
                            value={order.dose}
                            onChange={(event) => handleOrderChange(order.id, 'dose', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                          <TextField
                            label="투여/검사 빈도"
                            value={order.freq}
                            onChange={(event) => handleOrderChange(order.id, 'freq', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                        </Stack>
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mt: 2 }}>
                          <TextField
                            label="투여 경로 / 방법"
                            value={order.route}
                            onChange={(event) => handleOrderChange(order.id, 'route', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                          <TextField
                            label="일수"
                            value={order.days}
                            onChange={(event) => handleOrderChange(order.id, 'days', event.target.value)}
                            sx={{ flex: 1 }}
                          />
                        </Stack>
                        <TextField
                          label="비고"
                          value={order.notes}
                          onChange={(event) => handleOrderChange(order.id, 'notes', event.target.value)}
                          sx={{ mt: 2 }}
                          multiline
                          minRows={2}
                        />
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      추가된 처방이 없습니다. 상단 검색창에서 선택하세요.
                    </Typography>
                  )}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Stack>

        <Box
          sx={{
            gridColumn: '1 / -1',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 1,
            flexWrap: 'wrap'
          }}
        >
          <Button
            type="button"
            variant="outlined"
            onClick={() => {
              setNarrative('');
              setSocialHistory('');
              setFamilyHistory('');
              setSelectedDiagnoses([]);
              setSelectedOrders([]);
              setError(null);
              setVisitDate(dayjs());
            }}
            disabled={submitting}
          >
            초기화
          </Button>
          <Button type="submit" variant="contained" disabled={submitting || disableSubmit}>
            {submitting ? '저장 중…' : '기록 저장'}
          </Button>
        </Box>
      </Box>

      <Snackbar
        open={successOpen}
        autoHideDuration={4000}
        onClose={() => setSuccessOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          action={
            <IconButton size="small" color="inherit" onClick={() => setSuccessOpen(false)}>
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        >
          임상 기록이 저장되었습니다.
        </Alert>
      </Snackbar>
    </>
  );
};

export default NoteComposer;
