class DefaultTask:
    def load_schema(self, schema: dict, step_id: str):
        pass

    def run(self, cwd: str) -> bool:
        print("Starting build task")
        print("Finished build task")
        return True
