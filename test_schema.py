from mi.patient_creation.schemas import PatientProfile

patient = PatientProfile()

print(patient.model_dump_json(indent=4))