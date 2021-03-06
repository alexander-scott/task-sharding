import argparse


def parse_input_arguments(parser: argparse.ArgumentParser = None):
    if not parser:
        parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--client_id", help="Unique client identifier", required=True)
    parser.add_argument("--cache_id", help="Unique cache identifier", required=True)
    parser.add_argument("--schema_path", help="Path to Schema file", required=True)
    args = parser.parse_args()
    return args
