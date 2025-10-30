import { useEffect, useState } from 'react';
import { PatientDetailResponse } from '../types/patient';

const usePatientDetail = (patientId: number | null) => {
  const [detail, setDetail] = useState<PatientDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) {
      setDetail(null);
      setLoading(false);
      setError('환자 식별자가 필요합니다.');
      return;
    }

    let isMounted = true;
    const controller = new AbortController();

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/patients/${patientId}/`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error('환자 정보를 불러오는 데 실패했습니다.');
        }
        const payload: PatientDetailResponse = await response.json();
        if (isMounted) {
          setDetail(payload);
        }
      } catch (err) {
        if (!isMounted || controller.signal.aborted) {
          return;
        }
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDetail();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [patientId]);

  return { detail, loading, error };
};

export default usePatientDetail;
