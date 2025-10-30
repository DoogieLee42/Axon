export interface Patient {
  id: string;
  name: string;
  birthDate: string;
  sex: '남' | '여';
  phone: string;
  registrationNumber: string;
  primaryPhysician: string;
}

export interface VitalSigns {
  bp: string;
  pulse: string;
  temp: string;
  resp: string;
  height: string;
  weight: string;
  bmi: string;
}

export interface MedicationOrder {
  id: string;
  name: string;
  dose: string;
  instructions?: string;
}

export interface ClinicalNote {
  id: string;
  author: string;
  note: string;
  createdAt: string;
}
