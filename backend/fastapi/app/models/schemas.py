from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class HealthResponse(BaseModel):
    status: str


class AssessmentSummary(BaseModel):
    assessment_type: str
    total_responses: int
    highest_score: Optional[int]
    average_score: Optional[float]
    latest_timestamp: Optional[str]


class AssessmentEntry(BaseModel):
    id: int
    total_score: int
    details: Dict[str, Any]
    timestamp: str


class AssessmentDetail(BaseModel):
    assessment_type: str
    entries: List[AssessmentEntry]


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str


# Analytics schemas
class AgeGroupStats(BaseModel):
    """Aggregated statistics by age group"""
    age_group: str
    total_assessments: int
    average_score: float
    min_score: int
    max_score: int
    average_sentiment: float


class ScoreDistribution(BaseModel):
    """Score distribution for analytics"""
    score_range: str
    count: int
    percentage: float


class TrendDataPoint(BaseModel):
    """Time-series data point"""
    period: str
    average_score: float
    assessment_count: int


class AnalyticsSummary(BaseModel):
    """Overall analytics summary - aggregated data only"""
    total_assessments: int = Field(description="Total number of assessments")
    unique_users: int = Field(description="Number of unique users")
    global_average_score: float = Field(description="Overall average score")
    global_average_sentiment: float = Field(description="Overall sentiment score")
    age_group_stats: List[AgeGroupStats] = Field(description="Stats by age group")
    score_distribution: List[ScoreDistribution] = Field(description="Score distribution")
    assessment_quality_metrics: Dict[str, int] = Field(
        description="Quality metrics (rushed, inconsistent counts)"
    )


class TrendAnalytics(BaseModel):
    """Trend analytics over time"""
    period_type: str = Field(description="Time period type (daily, weekly, monthly)")
    data_points: List[TrendDataPoint] = Field(description="Time series data")
    trend_direction: str = Field(description="Overall trend (increasing, decreasing, stable)")


class BenchmarkComparison(BaseModel):
    """Benchmark comparison data"""
    category: str
    global_average: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_90: float


class PopulationInsights(BaseModel):
    """Population-level insights - no individual data"""
    most_common_age_group: str
    highest_performing_age_group: str
    total_population_size: int
    assessment_completion_rate: Optional[float] = Field(
        default=None, 
        description="Percentage of started assessments that were completed"
    )
