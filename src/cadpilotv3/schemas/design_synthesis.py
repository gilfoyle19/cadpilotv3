from pydantic import BaseModel

from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema


class DesignSynthesis(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    spec: IntentSpec
    geometry_plan: GeometryPlan
    parameters: ParameterSchema
    critic_a_report: CriticReport
