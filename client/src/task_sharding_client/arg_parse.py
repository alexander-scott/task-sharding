import argparse


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="inputs for script")
    parser.add_argument("--client_id", help="Unique client identifier", required=True)
    parser.add_argument("--cache_id", help="Unique cache identifier", required=True)
    parser.add_argument("--schema_path", help="Path to Schema file", required=True)
    parser.add_argument("--repo_state_path", help="Path to file containing repo state", required=True)
    parser.add_argument("--workspace_path", help="Path to workspace", required=False)
    args = parser.parse_args()
    return args
