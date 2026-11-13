
from pydantic import BaseModel, Field
from typing import Optional, Literal


class BasicInformation(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation_lifestyle: Optional[str] = None
    family_social_context: Optional[str] = None


class MainIssue(BaseModel):
    behavior_or_health_issue: Optional[str] = None
    duration: Optional[str] = None
    frequency_or_severity: Optional[str] = None
    current_situation: Optional[str] = None
    why_it_matters: Optional[str] = None


class Motivation(BaseModel):
    desire_to_change: Optional[str] = None
    reasons_for_change: list[str] = Field(default_factory=list)
    desired_improvements: list[str] = Field(default_factory=list)
    personal_values: list[str] = Field(default_factory=list)
    importance_of_change: Optional[str] = None


class Ambivalence(BaseModel):
    reasons_for_change: list[str] = Field(default_factory=list)
    reasons_against_change: list[str] = Field(default_factory=list)
    perceived_benefits_of_current_behavior: list[str] = Field(default_factory=list)
    perceived_disadvantages_of_current_behavior: list[str] = Field(default_factory=list)
    conflicting_goals: list[str] = Field(default_factory=list)

class ProvidedBehaviour(BaseModel):
    behaviour: str
    context: Optional[str] = None

class PreviousAttempts(BaseModel):
    attempted_before: Optional[bool] = None
    what_was_tried: list[str] = Field(default_factory=list)
    what_worked: list[str] = Field(default_factory=list)
    what_did_not_work: list[str] = Field(default_factory=list)
    reasons_for_return: list[str] = Field(default_factory=list)


class SocialEnvironment(BaseModel):
    family_influence: Optional[str] = None
    friends_and_peers: Optional[str] = None
    work_environment: Optional[str] = None
    living_situation: Optional[str] = None
    other_environmental_factors: list[str] = Field(default_factory=list)


class PatientProfile(BaseModel):
    basic_information: BasicInformation = Field(
        default_factory=BasicInformation
    )

    background: Optional[str] = None

    main_issue: MainIssue = Field(
        default_factory=MainIssue
    )

    motivation: Motivation = Field(
        default_factory=Motivation
    )

    ambivalence: Ambivalence = Field(
        default_factory=Ambivalence
    )

    previous_attempts: PreviousAttempts = Field(
        default_factory=PreviousAttempts
    )

    barriers: list[str] = Field(default_factory=list)

    beliefs_and_concerns: list[str] = Field(default_factory=list)

    social_environment: SocialEnvironment = Field(
        default_factory=SocialEnvironment
    )

    goals: list[str] = Field(default_factory=list)

    other_relevant_information: list[str] = Field(
        default_factory=list
    )

    trainee_provided_behaviour: list[ProvidedBehaviour] = Field(
    default_factory=list
    )


class PatientCreationTurn(BaseModel):
    assistant_message: str

    action: Literal[
        "ask_question",
        "clarify",
        "confirm_profile"
    ]

    patient_profile: PatientProfile

    missing_information: list[str] = Field(
        default_factory=list
    )

    contradictions: list[str] = Field(
        default_factory=list
    )
