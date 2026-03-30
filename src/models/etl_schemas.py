from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class MetadataSchema(BaseModel):
    year: Optional[int] = None
    box_office: Optional[int] = None
    directors: Optional[List[str]] = []
    genres: Optional[List[str]] = []
    wikidata_id: Optional[str] = None

class CastMappingSchema(BaseModel):
    actor: str
    external_id: str
    gender: Optional[int] = None
    birth_date: Optional[str] = None
    role: str
    guarantee_rank: Optional[str] = None

class ScenarioGraphDataSchema(BaseModel):
    scenario_title: str
    setting_period: str
    setting_location: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class ExtractedRecordSchema(BaseModel):
    external_id: str
    title: str
    metadata: Optional[MetadataSchema] = None
    plot_full: str
    setting_period: str
    setting_location: str
    scenario_graph_data: ScenarioGraphDataSchema
    original_cast_mapping: List[CastMappingSchema]
