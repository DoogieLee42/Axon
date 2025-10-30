import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { Patient } from '../types/patient';
import { nanoid } from 'nanoid';

type PatientInput = Omit<Patient, 'id'>;

interface PatientContextValue {
  patients: Patient[];
  registerPatient: (data: PatientInput) => void;
  getPatient: (id: string) => Patient | undefined;
}

const initialPatients: Patient[] = [
  {
    id: '1',
    name: '김하늘',
    birthDate: '1988-02-14',
    sex: '여',
    phone: '010-1234-5678',
    registrationNumber: '19880214-1234567',
    primaryPhysician: '이정민'
  },
  {
    id: '2',
    name: '박지훈',
    birthDate: '1979-09-02',
    sex: '남',
    phone: '010-7777-1414',
    registrationNumber: '19790902-7654321',
    primaryPhysician: '정세영'
  }
];

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [patients, setPatients] = useState<Patient[]>(initialPatients);

  const registerPatient = useCallback((data: PatientInput) => {
    setPatients((prev) => [
      ...prev,
      {
        id: nanoid(),
        ...data
      }
    ]);
  }, []);

  const value = useMemo(() => {
    const index = new Map<string, Patient>();
    patients.forEach((patient) => index.set(patient.id, patient));

    return {
      patients,
      registerPatient,
      getPatient: (id: string) => index.get(id)
    };
  }, [patients, registerPatient]);

  return <PatientContext.Provider value={value}>{children}</PatientContext.Provider>;
};

export const usePatientContext = () => {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error('usePatientContext must be used within PatientProvider');
  }
  return context;
};
