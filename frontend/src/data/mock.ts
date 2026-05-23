export type Patient = {
  id: string;
  firstName: string;
  lastName: string;
  dob: string;
  bloodType: string;
  allergies: string[];
  photoUrl?: string;
};

export type Medication = {
  id: string;
  name: string;
  dosage: string;
  time: string; // "08:00"
  block: "morning" | "afternoon" | "night";
  taken: boolean;
};

export type Appointment = {
  id: string;
  doctor: string;
  type: string;
  date: string; // ISO
  location: string;
  isVideo: boolean;
};

export type Caregiver = {
  id: string;
  name: string;
  relation: string;
  phone: string;
  photoUrl?: string;
};

export type AppNotification = {
  id: string;
  kind: "medication" | "appointment" | "message";
  label: string; // ≤ 6 words
  time: string;
};

export const patient: Patient = {
  id: "p1",
  firstName: "Margaret",
  lastName: "Hollis",
  dob: "1942-03-14",
  bloodType: "O+",
  allergies: ["Penicillin", "Latex"],
};

export const initialMedications: Medication[] = [
  { id: "m1", name: "Lisinopril", dosage: "10 mg", time: "08:00", block: "morning", taken: false },
  { id: "m2", name: "Metformin", dosage: "500 mg", time: "13:00", block: "afternoon", taken: false },
  { id: "m3", name: "Atorvastatin", dosage: "20 mg", time: "21:00", block: "night", taken: false },
];

export const appointments: Appointment[] = [
  { id: "a1", doctor: "Dr. Chen", type: "Cardiology", date: "2026-05-26T10:00:00", location: "Clinic, Room 204", isVideo: false },
  { id: "a2", doctor: "Dr. Patel", type: "Follow-up", date: "2026-05-29T14:30:00", location: "Video call", isVideo: true },
  { id: "a3", doctor: "Dr. Adams", type: "Home visit", date: "2026-06-02T09:00:00", location: "Home", isVideo: false },
  { id: "a4", doctor: "Dr. Lin", type: "Physiotherapy", date: "2026-06-05T11:00:00", location: "Clinic, Room 110", isVideo: false },
];

export const caregivers: Caregiver[] = [
  { id: "c1", name: "Sarah Hollis", relation: "Daughter", phone: "+1 555 0101" },
  { id: "c2", name: "Nurse Daniel", relation: "Home nurse", phone: "+1 555 0144" },
];

export const notifications: AppNotification[] = [
  { id: "n1", kind: "medication", label: "Morning pill due", time: "08:00" },
  { id: "n2", kind: "appointment", label: "Dr. Chen tomorrow", time: "10:00" },
  { id: "n3", kind: "message", label: "Sarah sent a note", time: "Yesterday" },
  { id: "n4", kind: "medication", label: "Evening pill at 9", time: "21:00" },
  { id: "n5", kind: "appointment", label: "Home visit Tuesday", time: "09:00" },
];
