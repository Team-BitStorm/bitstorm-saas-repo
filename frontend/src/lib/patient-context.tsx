import * as React from "react";
import {
  patient as mockPatient,
  initialMedications,
  appointments as mockAppointments,
  caregivers as mockCaregivers,
  notifications as mockNotifications,
  type Medication,
} from "@/data/mock";

type Ctx = {
  patient: typeof mockPatient;
  medications: Medication[];
  appointments: typeof mockAppointments;
  caregivers: typeof mockCaregivers;
  notifications: typeof mockNotifications;
  markMedicationTaken: (id: string, taken: boolean) => void;
};

const PatientCtx = React.createContext<Ctx | null>(null);

export function PatientProvider({ children }: { children: React.ReactNode }) {
  const [medications, setMedications] = React.useState<Medication[]>(initialMedications);

  const markMedicationTaken = React.useCallback((id: string, taken: boolean) => {
    setMedications((prev) => prev.map((m) => (m.id === id ? { ...m, taken } : m)));
  }, []);

  const value = React.useMemo<Ctx>(
    () => ({
      patient: mockPatient,
      medications,
      appointments: mockAppointments,
      caregivers: mockCaregivers,
      notifications: mockNotifications,
      markMedicationTaken,
    }),
    [medications, markMedicationTaken],
  );

  return <PatientCtx.Provider value={value}>{children}</PatientCtx.Provider>;
}

export function usePatient() {
  const ctx = React.useContext(PatientCtx);
  if (!ctx) throw new Error("usePatient must be used inside PatientProvider");
  return ctx;
}
