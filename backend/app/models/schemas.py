"""Pydantic API schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list = Field(default_factory=list)
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    status: str


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    created_at: str
    chunk_count: int
    processing_status: str


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int


class DocumentDetailResponse(BaseModel):
    document_id: str
    filename: str
    created_at: str
    updated_at: str
    byte_size: int
    chunk_count: int
    processing_status: str
    processing_error: str | None = None
    preview: str | None = None


class DocumentContentResponse(BaseModel):
    document_id: str
    filename: str
    content_text: str


class ChunkItem(BaseModel):
    chunk_id: str
    chunk_index: int
    text: str
    char_start: int | None = None
    char_end: int | None = None


class ChunkListResponse(BaseModel):
    document_id: str
    items: list[ChunkItem]
    total: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    document_ids: list[str] | None = None
    collection_id: str | None = None
    min_score: float | None = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    snippet: str
    score: float
    char_start: int | None = None
    char_end: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    model: str
    top_k: int
    duration_ms: float


class Citation(BaseModel):
    citation_id: str
    chunk_id: str
    document_id: str
    filename: str
    snippet: str
    score: float | None = None
    char_start: int | None = None
    char_end: int | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] | None = None
    top_k: int | None = Field(default=None, ge=1, le=50)
    conversation_id: str | None = None
    session_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    insufficient_evidence: bool = False
    retrieval: dict
    request_id: str
    session_id: str | None = None


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(default="", max_length=4000)


class CollectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)


class CollectionResponse(BaseModel):
    collection_id: str
    name: str
    description: str
    document_count: int
    created_at: str


class CollectionDocumentRequest(BaseModel):
    document_id: str


class SessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=512)


class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class SessionMessageResponse(BaseModel):
    message_id: str
    question: str
    answer: str
    citations: list[Citation]
    created_at: str


class EvalRunRequest(BaseModel):
    dataset_name: str = Field(default="golden")
    top_k: int = Field(default=5, ge=1, le=50)


class EvalRunResponse(BaseModel):
    run_id: str
    dataset_name: str
    metrics: dict
    config: dict
    created_at: str


class ResearchRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] | None = None
    conversation_id: str | None = None


class AgentStep(BaseModel):
    step_index: int
    tool: str
    tool_input: dict
    observation_summary: str


class ResearchResponse(BaseModel):
    answer: str
    citations: list[Citation]
    steps: list[AgentStep]
    status: str
    request_id: str


class PublicSettingsResponse(BaseModel):
    app_name: str
    app_env: str
    embedding_provider: str
    embedding_model_name: str
    llm_provider: str
    retrieval_top_k: int
    max_upload_bytes: int
    allowed_upload_extensions: list[str]
    demo_mode: bool
    agent_enabled: bool


class SystemStatusResponse(BaseModel):
    status: str
    database: str
    document_count: int
    chunk_count: int
    embedding_model: str
    llm_provider: str
    version: str
