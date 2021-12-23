import yaml


class SchemaLoader:
    @staticmethod
    def load_schema(path: str) -> dict:
        with open(path) as file:
            return yaml.safe_load(file)
