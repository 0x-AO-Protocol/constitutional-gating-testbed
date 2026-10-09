# brain_cloud_openclaw/schemas_openclaw.py
# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class TierType(str, Enum):
    TIER_0 = "TIER_0_INTERVIEW"
    TIER_1 = "TIER_1_RESEARCH"
    TIER_2 = "TIER_2_ANALYSIS"
    TIER_3 = "TIER_3_INTEGRATION"

class PillarType(str, Enum):
    PILLAR_1 = "CUSTOMER_PAIN_DESIRE"
    PILLAR_2 = "OFFER_UNIQUENESS"
    PILLAR_3 = "OPERATOR_TRUST"
    PILLAR_4 = "UNIT_ECONOMICS"
    PILLAR_5 = "EXECUTION_SUSTAINABILITY"

# =====================================================================
# 1. Thinking OS: 5-Pillar Constitution Data Model
# =====================================================================
class IndividualPillarSchema(BaseModel):
    core_concept: str = Field(..., description="The core strategy or definition for each specific pillar.")
    constraints: List[str] = Field(default=[], description="Absolute behavioral constraints and boundary conditions that must never be violated.")
    validation_metrics: List[str] = Field(..., description="Qualitative evaluation metrics used by Monitor AI to gauge fitness score.")

class FivePillarConstitution(BaseModel):
    version: str = Field("v2.1", description="The version control number of the constitution.")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pillar_1_pain: IndividualPillarSchema = Field(..., alias="CUSTOMER_PAIN_DESIRE")
    pillar_2_offer: IndividualPillarSchema = Field(..., alias="OFFER_UNIQUENESS")
    pillar_3_trust: IndividualPillarSchema = Field(..., alias="OPERATOR_TRUST")
    pillar_4_economics: IndividualPillarSchema = Field(..., alias="UNIT_ECONOMICS")
    pillar_5_sustainability: IndividualPillarSchema = Field(..., alias="EXECUTION_SUSTAINABILITY")

    @field_validator("pillar_4_economics")
    @classmethod
    def verify_pricing_strategy(cls, v: IndividualPillarSchema) -> IndividualPillarSchema:
        required_rule = "Prohibition of discounting"
        if not any(required_rule in c for c in v.constraints):
            raise ValueError(f"CRITICAL_VALIDATION_ERROR: The required constraint '{required_rule}' is missing from Pillar 4. Triggering Auto-Correction.")
        return v

    @field_validator("pillar_5_sustainability")
    @classmethod
    def verify_security_constraints(cls, v: IndividualPillarSchema) -> IndividualPillarSchema:
        required_rule = "Absolute ban on external URL clicks"
        if not any(required_rule in c for c in v.constraints):
            raise ValueError(f"CRITICAL_VALIDATION_ERROR: The required constraint '{required_rule}' is missing from Pillar 5. Triggering Auto-Correction.")
        return v

# =====================================================================
# 2. Orchestration: Cross-Tier Micro-State JSON Model
# =====================================================================
class MicroStateContext(BaseModel):
    transaction_id: str = Field(..., description="A unique UUID used to trace and monitor an ongoing workflow sequence.")
    current_tier: TierType = Field(..., description="The specific computational tier currently executing the task.")
    target_lead_id: Optional[str] = Field(None, description="The unique identification ID of the prospective client in Pipeline 2.")
    last_action_status: Literal["SUCCESS", "FAILED", "PENDING_HITL"] = Field("SUCCESS")
    failed_attempts_count: int = Field(default=0, description="The number of consecutive failed or rejected attempts for the identical sub-task (N).")
    
    structured_payload: Dict[str, str] = Field(
        default_factory=dict, 
        description="A plain key-value data container designed to minimize LLM context window utilization."
    )

# =====================================================================
# 3. Asynchronous Mediation: Absolute H.I.T.L. & SSE Streaming Model
# =====================================================================
class HITLStatus(str, Enum):
    AWAITING = "SUSPENDED_AWAITING_EDGE_EVENT"
    APPROVED = "RELEASED_APPROVED"
    REJECTED = "RELEASED_REJECTED"

class HITLApprovalRequest(BaseModel):
    state_id: str = Field(..., description="The independent state identifier corresponding to UUID_ST_1 through UUID_ST_9.")
    transaction_id: str = Field(..., description="The transaction ID cross-referenced with the current Micro-State.")
    action_type: str = Field(..., description="The designated action type requiring verification (e.g., LINKEDIN_DM_TRANSACTION).")
    payload_preview: str = Field(..., description="The generated message or artifact snippet to be evaluated by the user on the dashboard UI.")
    requires_approval: bool = Field(default=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HITLApprovalResponse(BaseModel):
    state_id: str = Field(...)
    transaction_id: str = Field(...)
    status: Literal["APPROVE", "REJECT"] = Field(...)
    feedback_comment: Optional[str] = Field(None, description="The corrective feedback input provided by the user in the event of a REJECT status.")

class SSEDiegeticStreamPayload(BaseModel):
    transaction_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_tier: TierType = Field(...)
    agent_persona_name: str = Field(..., description="The name of the agent actively processing or debating (e.g., RedTeam_Agent).")
    thought_process_log: str = Field(..., description="The real-time log capturing multi-agent debate dynamics or X/Y/Z-axis scoring analytics calculated by Monitor AI.")

# =====================================================================
# 4. Output Validation: Hard Gate for Strategic Pivot (New in v2.1)
# =====================================================================
class SalesPitchOutput(BaseModel):
    """
    Strict validation schema enforcing the 'Hypothesis-driven Pain Scan' 
    on Tier 3 output before routing to the Target Endpoint.
    """
    pitch_text: str = Field(..., description="The raw sales or negotiation text generated by Tier 3.")
    contains_hypothesis_question: bool = Field(..., description="Must be true if a strategic hypothesis probing the target's internal pain is present.")
    hypothesis_target_pillar: int = Field(1, description="Always tied to Pillar 1 (Customer Pain & Desire).")

    @field_validator("pitch_text")
    @classmethod
    def check_hypothesis_format(cls, v: str, info) -> str:
        # Hard Gate Validation: Ensure the text physically contains a question mark (?) to pass the hypothesis scan
        if "?" not in v:
            raise ValueError(
                "CRITICAL_OUTPUT_ERROR: Generated pitch text does not contain any hypothesis question mark (?). "
                "The agent failed the 'Hypothesis-driven Pain Scan' gate. Triggering instant Auto-Correction."
            )
        return v
