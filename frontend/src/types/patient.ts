export type GenderCode = 'M' | 'F' | 'U';

export interface PatientSummary {
  id: number;
  name: string;
  gender: GenderCode;
  birthDate: string;
  age: number;
  rrn: string;
  phone: string;
  address: string;
  regNo: string;
  createdAt: string;
}

export interface VitalSnapshot {
  systolic: number | null;
  diastolic: number | null;
  heartRate: number | null;
  respRate: number | null;
  temperatureC: number | null;
  spo2: number | null;
  painScore: number | null;
}

export interface AnthropometricsSnapshot {
  heightCm: number | null;
  weightKg: number | null;
  bmi: number | null;
  waistCm: number | null;
}

export interface MedicationSummary {
  id: number;
  name: string;
  dose: string;
  freq: string;
  route: string;
  durationDays: number;
}

export interface DiagnosisSummary {
  id: number;
  code: string;
  name: string;
  source: string;
  recordedAt: string;
}

export interface AllergySummary {
  id: number;
  substance: string;
  reaction: string;
  severity: string;
  notes: string;
}

export interface PrescriptionSummary {
  id: number;
  itemType: string;
  name: string;
  dose: string;
  freq: string;
  days: number;
  notes: string;
}

export interface ClinicalNoteSummary {
  id: number;
  visitDate: string;
  chiefComplaint: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  primaryIcd: string;
  medications: MedicationSummary[];
  diagnoses: DiagnosisSummary[];
  allergies: AllergySummary[];
  prescriptions: PrescriptionSummary[];
  vitals: VitalSnapshot | null;
  anthropometrics: AnthropometricsSnapshot | null;
}

export interface ExternalDocumentSummary {
  id: number;
  title: string;
  source: string;
  recordedAt: string | null;
  description: string;
  fileUrl: string;
}

export interface PatientDetailResponse {
  patient: PatientSummary;
  notes: ClinicalNoteSummary[];
  latestVitals: VitalSnapshot | null;
  latestAnthropometrics: AnthropometricsSnapshot | null;
  documents: ExternalDocumentSummary[];
}

export interface CreatePatientInput {
  name: string;
  gender: GenderCode;
  birthDate: string;
  rrn: string;
  phone: string;
  address: string;
}
