class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: List[str]
