"""Fake user generator.

This module generates fake users and stores them in a tinydb database.
These user are generated using the faker library with a little bit of LLM magic.

Goal is having a user base for a virtual forum.

fields:

real_name:
user_name:
gender:
age:
alignment:
bio:
email:
interests (real life):
interests (virtual, online):
political_views:
social_views:

"""

import random
from datetime import date

from faker import Faker
from pydantic import BaseModel, Field
from rich.console import Console
from tinydb import TinyDB

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.utils.settings import APP_SETTINGS

fake = Faker()
console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/05_fakeuser_generator"

db = TinyDB(f"{APP_SETTINGS.DATA_FOLDER}/db.json")


class User(BaseModel):
    """User model."""

    real_name: str = Field(..., title="Real Name")
    user_name: str = Field(..., title="User Name")
    gender: str = Field(..., title="gender")
    birthday: str = Field(..., title="Birthday")
    age: int = Field(..., title="Age")
    alignment: str = Field(..., title="Alignment")
    bio: str = Field(..., title="Bio")
    job: str = Field(..., title="Job")
    email: str = Field(..., title="Email")
    interests_real: str = Field(..., title="Interests (real life)")
    interests_virtual: str = Field(..., title="Interests (virtual, online)")
    political_views: str = Field(..., title="Political Views")
    social_views: str = Field(..., title="Social Views")


# Agents

user_generator = Agent(name="User Generator", configs=[LiteLLMConfig()])  # a("user",llm())
bio_generator = Agent(name="Biography Generator", configs=[LiteLLMConfig()])

# Instructions


def instruction_user_generator(context_variables: ContextVariables) -> str:  # noqa: D103
    instruction = """
    You are a helpful agent specialized in choosing the right tool for the task at hand.
    Task: Generating fake users for a virtual forum.
    """
    return instruction


def instruction_bio_generator(context_variables: ContextVariables) -> str:  # noqa: D103
    instruction = """
    You are a helpful agent specialized in choosing the right tool for the task at hand.
    Task: Generate a bio for a fake user.
    """
    return instruction


user_generator.instructions = instruction_user_generator
bio_generator.instructions = instruction_bio_generator


# Functions


def get_random_alignment() -> str:
    """Get a random alignment."""
    algnmt = random.randint(1, 9)
    alignment = "True Neutral"
    if algnmt == 1:
        alignment = "Lawful Good"
    elif algnmt == 2:
        alignment = "Neutral Good"
    elif algnmt == 3:
        alignment = "Chaotic Good"
    elif algnmt == 4:
        alignment = "Lawful Neutral"
    elif algnmt == 5:
        alignment = "True Neutral"
    elif algnmt == 6:
        alignment = "Chaotic Neutral"
    elif algnmt == 7:
        alignment = "Lawful Evil"
    elif algnmt == 8:
        alignment = "Neutral Evil"
    elif algnmt == 9:
        alignment = "Chaotic Evil"
    return alignment


def get_gender() -> str:
    """Get a random gender."""
    r = random.randint(0, 100)
    gender = "M"
    if r > 80:
        gender = "F"
    return gender


def get_birthdate() -> date:
    """Get a random birthdate."""
    return fake.date_of_birth(minimum_age=18, maximum_age=80)


def transfer_user_data_to_biography_generator(context_variables: ContextVariables) -> Result:
    """Generate a bio for a user."""
    # Generate some fields with faker

    # Gender with a 80% chance of being male and 20% of being female
    from schwarm.models.agent import Agent

    profile = fake.profile(sex=get_gender())  # type: ignore
    birthdate = get_birthdate()

    user = User(
        real_name=str(profile["name"]),
        user_name="",
        gender=str(profile["sex"]),
        birthday=str(birthdate),
        age=2024 - birthdate.year,  # type: ignore
        alignment=get_random_alignment(),  # type: ignore
        bio="",
        job=str(profile["job"]),
        email=str(profile["mail"]),
        interests_real="",
        interests_virtual="",
        political_views="",
        social_views="",
    )
    context_variables["user"] = user
    agent: Agent = bio_generator
    return Result(value=f"{user}", context_variables=context_variables, agent=agent)


def transfer_user_bio_to_user_generator(
    context_variables: ContextVariables,
    user_name: str,
    biography: str,
    interests_real: str,
    interests_virtual: str,
    political_views: str,
    social_views: str,
) -> Result:
    """Save user bio to database.

    The bio should be a short, but informative text that gives a clear picture of the user.
    It should fit the alignment of the user, and the rest of the profile, like age and job

    Arguments:
        user_name: The user name of the user. The more creative the better.
        biography: The biography of the user. Short, but informative. Should give a clear picture of the user.
        interests_real: The real life interests of the user. comma separated tags.
        interests_virtual: The virtual interests of the user. comma separated tags.
        political_views: The political views of the user. comma separated tags.
        social_views: The social views of the user. comma separated tags.
    """
    user = context_variables["user"]
    if "count" in context_variables:
        context_variables["count"] += 1
    else:
        context_variables["count"] = 1
    count = context_variables["count"]
    if isinstance(user, User):
        user.bio = biography
        user.user_name = user_name
        user.interests_real = interests_real
        user.interests_virtual = interests_virtual
        user.political_views = political_views
        user.social_views = social_views
    context_variables["user"] = user
    db.insert(user.dict())  # type: ignore
    console.print(f"User {context_variables['count']}:\n{biography}")
    return Result(value=f"User #{count}: {user}", context_variables=context_variables, agent=user_generator)


user_generator.functions = [transfer_user_data_to_biography_generator]
bio_generator.functions = [transfer_user_bio_to_user_generator]

response = Schwarm(interaction_mode="stop_and_go").quickstart(user_generator, "Start generating!")
