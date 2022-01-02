class RepoStateParser:
    @staticmethod
    def parse_repo_state(path_to_repo_state: str) -> dict:
        return {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
                # "additional_patchsets": [
                #     "ee36655f9fd3c76c21363a8b32e1569fa332c819",
                #     "05c0d07a9d0354be8cc1696fae01c9322a33c18e",
                # ],
            }
        }
