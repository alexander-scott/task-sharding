import uuid


class SchemaDetails:
    def __init__(self, cache_id: str, schema_id: str, total_tasks: int) -> None:
        self.cache_id = cache_id
        self.schema_id = schema_id
        self.total_tasks = total_tasks
        self.id = str(uuid.uuid4())
