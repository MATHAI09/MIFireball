from .agent import CharacterCreationAgent


# =========================================
# 1. Display Character Collection
# =========================================

def display_characters(collection):

    print("\n" + "=" * 65)
    print(f"CHARACTERS FOR {collection.patient_name.upper()}")
    print("=" * 65)

    for index, character in enumerate(
        collection.characters,
        start=1
    ):

        state = character.initial_emotional_state

        print(f"\n{index}. {character.character_name}")
        print("-" * 55)

        print(f"Character ID: {character.character_id}")
        print(f"Type: {character.character_type}")
        print(f"Description: {character.description}")

        print("\nPersonality traits:")
        for trait in character.personality_traits:
            print(f"  - {trait}")

        print("\nEmotional tendencies:")
        for tendency in character.emotional_tendencies:
            print(f"  - {tendency}")

        print("\nCommunication style:")
        print(f"  {character.communication_style.description}")
        for characteristic in (
            character.communication_style.characteristics
        ):
            print(f"  - {characteristic}")

        print("\nBehavioural characteristics:")
        for behaviour in (
            character.behavioural_characteristics.trainee_provided
        ):
            print(f"  - {behaviour} [Trainee provided]")

        for behaviour in (
            character.behavioural_characteristics.generated
        ):
            print(f"  - {behaviour} [Generated]")

        print("\nAttitude towards change:")
        attitude = character.attitude_towards_change
        print(f"  Readiness: {attitude.readiness}")
        print(f"  Openness: {attitude.openness}")
        print(f"  Confidence: {attitude.confidence}")

        print("\nInitial emotional state:")
        print(f"  Frustration: {state.frustration}/10")
        print(f"  Anxiety: {state.anxiety}/10")
        print(f"  Trust: {state.trust}/10")
        print(f"  Motivation: {state.motivation}/10")
        print(f"  Confidence: {state.confidence}/10")
        print(
            f"  Willingness to discuss: "
            f"{state.willingness_to_discuss}/10"
        )
        print(
            f"  Willingness to change: "
            f"{state.willingness_to_change}/10"
        )

        print("\nInitial state explanation:")
        print(f"  {character.initial_state_explanation}")

    print("\n" + "=" * 65)


# =========================================
# 2. Local Confirmation Step (no LLM call)
# =========================================

def confirm_and_save(agent, turn):
    """
    Ask the trainee for explicit confirmation.

    Returns:
        "saved"   -> collection confirmed and saved
        "modify"  -> trainee wants to change something (turn updated)
        "exit"    -> trainee cancelled
        "invalid" -> invalid menu choice
    """

    print("\nAre you satisfied with the complete collection?")
    print("1. Yes, confirm and save")
    print("2. No, make further modifications")
    print("3. Exit")

    choice = input("\nEnter choice: ").strip()

    if choice == "1":

        agent.confirmation_pending = True
        agent.trainee_confirmed = True

        turn.action = "confirm_collection"
        turn.character_collection.status = "confirmed"

        agent.save_collection(turn)

        print("\nThe collection has been confirmed.")
        print("\nCharacter creation completed successfully!")
        return "saved", turn

    if choice == "2":

        modification = input("\nWhat would you like to change? ")

        if not modification.strip():
            print("Please enter a modification.")
            return "invalid", turn

        agent.confirmation_pending = False
        agent.trainee_confirmed = False

        turn = agent.respond(modification)
        return "modify", turn

    if choice == "3":

        print("\nCharacter creation cancelled.")
        return "exit", turn

    print("\nInvalid choice.")
    return "invalid", turn


# =========================================
# 3. Main Application
# =========================================

def main():

    print("=" * 65)
    print("          MOTIVATIONAL INTERVIEW TRAINER")
    print("               CHARACTER CREATION")
    print("=" * 65)

    try:

        print("\nInitializing Character Creation Agent...\n")

        agent = CharacterCreationAgent()

        print("Agent initialized successfully!")

        # -----------------------------------------
        # Generate initial characters
        # -----------------------------------------

        turn = agent.start()

        # Only reprint the characters when they have changed
        show = True

        while True:

            if show:
                print("\nCHARACTER CREATION AGENT:")
                print(turn.assistant_message)
                display_characters(turn.character_collection)

            show = True

            # -----------------------------------------
            # Present characters (first menu)
            # -----------------------------------------

            if turn.action == "present_characters":

                print("\nWhat would you like to do?")
                print("1. Modify a character")
                print("2. Create another character")
                print("3. Proceed with these characters")
                print("4. Exit")

                choice = input("\nEnter choice: ").strip()

                if choice == "1":

                    character_name = input(
                        "\nEnter the character name or ID: "
                    ).strip()

                    modification = input(
                        "Describe the modifications: "
                    ).strip()

                    if not character_name or not modification:
                        print("\nBoth fields are required.")
                        show = False
                        continue

                    message = (
                        f"Modify {character_name}. "
                        f"Requested modifications: {modification}"
                    )

                elif choice == "2":

                    description = input(
                        "\nDescribe the new character: "
                    ).strip()

                    if not description:
                        print("\nA description is required.")
                        show = False
                        continue

                    message = (
                        "Create an additional character. "
                        f"Requirements: {description}"
                    )

                elif choice == "3":

                    # Go straight to local confirmation, no LLM call
                    turn.action = "confirm_collection"
                    turn.character_collection.status = (
                        "awaiting_confirmation"
                    )

                    # Characters were just displayed, do not reprint
                    show = False
                    continue

                elif choice == "4":

                    print("\nCharacter creation cancelled.")
                    break

                else:

                    print("\nInvalid choice.")
                    show = False
                    continue

                turn = agent.respond(message)
                continue

            # -----------------------------------------
            # Handle refinement
            # -----------------------------------------

            if turn.action == "ask_question":

                print("\nYou can:")
                print("- Request further modifications")
                print("- Create another character")
                print("- Type 'ready' to move to final confirmation")
                print("- Type 'exit' to leave")

                user_input = input("\nYOU: ").strip()

                if user_input.lower() in ["exit", "quit"]:
                    print("\nCharacter creation session ended.")
                    break

                if not user_input:
                    print("Please enter a response.")
                    show = False
                    continue

                if user_input.lower() in ["ready", "done", "confirm"]:
                    turn.action = "confirm_collection"
                    turn.character_collection.status = (
                        "awaiting_confirmation"
                    )
                    show = False
                    continue

                turn = agent.respond(user_input)
                continue

            # -----------------------------------------
            # Handle final confirmation
            # -----------------------------------------

            if turn.action == "confirm_collection":

                # If the model itself returned a confirmed collection
                if (
                    turn.character_collection.status == "confirmed"
                    and agent.confirmation_pending
                ):

                    agent.trainee_confirmed = True
                    agent.save_collection(turn)

                    print("\nThe collection has been confirmed.")
                    print("\nCharacter creation completed successfully!")
                    break

                result, turn = confirm_and_save(agent, turn)

                if result in ("saved", "exit"):
                    break

                if result == "invalid":
                    show = False

                # "modify": turn was updated by the agent, reprint it
                continue

            # Unknown action, avoid an infinite loop
            print(f"\nUnexpected action: {turn.action}")
            break

    except Exception as error:

        print(f"\nError: {error}")

        print("\nCharacter creation could not be completed.")


if __name__ == "__main__":
    main()