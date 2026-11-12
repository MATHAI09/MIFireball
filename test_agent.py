from mi.patient_creation.agent import PatientCreationAgent


agent = PatientCreationAgent()

response = agent.start()

print("\nAGENT:")
print(response.assistant_message)

print("\nACTION:")
print(response.action)

print("\nPATIENT PROFILE:")
print(response.patient_profile.model_dump_json(indent=4))