from dataclasses import dataclass
import uuid


@dataclass
class SchemaDetails:
    cache_id: str
    branch: str
    schema_id: str
    total_steps: int
    id: str = str(uuid.uuid4())
