import { usePatientContext } from '../context/PatientContext';

const usePatients = () => {
  return usePatientContext();
};

export default usePatients;
