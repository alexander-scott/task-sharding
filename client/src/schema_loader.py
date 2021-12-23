import yaml


class SchemaLoader:
    @staticmethod
    def load_schema(path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)
