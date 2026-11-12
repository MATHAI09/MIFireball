
import json

from pathlib import Path

from .agent import PatientCreationAgent


def save_patient_profile(profile):

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / "patient_profile.json"

    with open(file_path, "w", encoding="utf-8") as file:

        json.dump(
            profile.model_dump(),
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nPatient profile saved: {file_path}")


def main():

    print("=" * 55)
    print("       MOTIVATIONAL INTERVIEW TRAINER")
    print("             PATIENT CREATION")
    print("=" * 55)

    print("\nInitializing agent...\n")

    agent = PatientCreationAgent()

    print("Agent initialized successfully!")

    # Start conversation
    turn = agent.start()

    while True:

        print("\nPATIENT CREATION AGENT:")
        print(turn.assistant_message)

        # Check if the agent is requesting confirmation
        if turn.action == "confirm_profile":

            print("\n" + "=" * 55)
            print("PATIENT PROFILE SUMMARY")
            print("=" * 55)

            print(
                turn.patient_profile.model_dump_json(indent=4)
            )

            answer = input(
                "\nIs this patient profile accurate? (yes/no): "
            ).strip().lower()

            if answer in ["yes", "y"]:

                save_patient_profile(turn.patient_profile)

                print("\nPatient profile confirmed!")
                print("Patient creation completed.")

                break

            elif answer in ["no", "n"]:

                correction = input(
                    "\nWhat would you like to change? "
                )

                turn = agent.respond(correction)

                continue

            else:

                print("Please enter yes or no.")
                continue

        # Normal conversation
        user_input = input("\nYOU: ").strip()

        if user_input.lower() in ["exit", "quit"]:

            print("\nPatient creation session ended.")

            break

        if not user_input:
            print("Please enter a response.")
            continue

        try:

            turn = agent.respond(user_input)

        except Exception as e:

            print(f"\nError: {e}")
            print("Please try again.")

            continue


if __name__ == "__main__":

    main()
