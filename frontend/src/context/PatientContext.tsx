import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { CreatePatientInput, PatientSummary } from '../types/patient';
import { getCsrfToken } from '../utils/csrf';

interface PatientContextValue {
  patients: PatientSummary[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  registerPatient: (input: CreatePatientInput) => Promise<PatientSummary | null>;
  findPatient: (id: number) => PatientSummary | undefined;
}

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/patients/', {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('환자 목록을 불러오지 못했습니다.');
      }
      const payload = await response.json();
      setPatients(Array.isArray(payload.results) ? payload.results : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const registerPatient = useCallback(
    async (input: CreatePatientInput) => {
      try {
        setError(null);
        const response = await fetch('/api/patients/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          credentials: 'include',
          body: JSON.stringify(input)
        });

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.error || '환자 등록에 실패했습니다.');
        }

        const patient: PatientSummary = await response.json();
        setPatients((prev) => [patient, ...prev]);
        return patient;
      } catch (err) {
        setError(err instanceof Error ? err.message : '환자 등록에 실패했습니다.');
        return null;
      }
    },
    []
  );

  const value = useMemo<PatientContextValue>(() => {
    const index = new Map<number, PatientSummary>();
    patients.forEach((patient) => index.set(patient.id, patient));

    return {
      patients,
      loading,
      error,
      refresh: fetchPatients,
      registerPatient,
      findPatient: (id: number) => index.get(id)
    };
  }, [patients, loading, error, fetchPatients, registerPatient]);

  return <PatientContext.Provider value={value}>{children}</PatientContext.Provider>;
};

export const usePatientContext = () => {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error('usePatientContext must be used within PatientProvider');
  }
  return context;
};
