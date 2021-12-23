import argparse


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--client_id", help="Client identifier", required=True)
    parser.add_argument("--schema_path", help="Path to Schema file", required=True)
    parser.add_argument("--workspace_path", help="Path to workspace", required=True)
    args = parser.parse_args()
    return args
