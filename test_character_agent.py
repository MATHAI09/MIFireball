from mi.character_creation.agent import CharacterCreationAgent

agent = CharacterCreationAgent()

print("Character Creation Agent initialized successfully!")

print("\nLoaded patient:")
print(
    agent.patient_profile["basic_information"]["name"]
)