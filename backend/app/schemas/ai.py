from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AiChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="User question to the AI Sustainability Advisor")


class CalculationBreakdown(BaseModel):
    formula: str
    inputs: Dict[str, Any]
    assumptions: Optional[List[str]] = None
    result: str


class StructuredCategoryItem(BaseModel):
    name: str
    emissions_kg: float
    record_count: Optional[int] = None
    percentage_of_gross: Optional[float] = None
    percentage_of_net: Optional[float] = None
    status: str = "positive"  # "positive" | "negative_credit" | "zero"
    note: Optional[str] = None


class LargestSourceInfo(BaseModel):
    category: str
    emissions_kg: float
    percentage_of_gross: float
    percentage_of_net: Optional[float] = None
    record_count: int


class RecommendationItem(BaseModel):
    title: str
    explanation: str
    expected_benefit: str
    priority: str = "Medium"  # "High" | "Medium" | "Low"
    category: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None


class KeyFindingItem(BaseModel):
    title: str
    description: str
    category: Optional[str] = None


class MetricItem(BaseModel):
    label: str
    value: Any
    unit: Optional[str] = None
    subtext: Optional[str] = None
    trend: Optional[str] = None  # "up" | "down" | "neutral"


class StructuredAiPayload(BaseModel):
    intent: Optional[str] = "direct"  # "direct" | "analytical" | "comparative" | "recommendation" | "comprehensive"
    direct_answer: str
    explanation: Optional[str] = None
    reporting_period: Optional[str] = None
    metrics: List[MetricItem] = Field(default_factory=list)
    key_findings: List[KeyFindingItem] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
    confidence_score: Optional[str] = None


class SustainabilityReport(BaseModel):
    status: str = "success"
    title: str = "Carbon Footprint & Sustainability Analysis"
    summary: str
    reporting_period: Optional[str] = None
    total_net_emissions_kg: float
    total_gross_emissions_kg: float
    total_records_analyzed: int
    largest_source: Optional[LargestSourceInfo] = None
    categories: List[StructuredCategoryItem] = Field(default_factory=list)
    key_findings: List[KeyFindingItem] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)


class AiChatResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    timestamp: str
    calculation_breakdown: Optional[CalculationBreakdown] = None
    suggested_follow_ups: List[str] = Field(default_factory=list)
    structured_report: Optional[Dict[str, Any]] = None
    structured_payload: Optional[StructuredAiPayload] = None
    meta: Optional[Dict[str, Any]] = None
