import uuid

from dataclasses import dataclass


@dataclass
class SchemaDetails:
    cache_id: str
    schema_id: str
    total_steps: int
    id: str = str(uuid.uuid4())
