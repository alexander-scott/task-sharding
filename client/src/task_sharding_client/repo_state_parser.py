import re
import subprocess


class RepoStateParser:
    @staticmethod
    def parse_repo_state() -> dict:
        default_branch = RepoStateParser.get_default_branch()
        repo_name = RepoStateParser.get_current_repo_name()
        current_patchset = RepoStateParser.get_current_patchset()

        return {
            repo_name: {
                "base_ref": default_branch,
                "patchset": current_patchset,
            },
        }

    @staticmethod
    def get_default_branch() -> str:
        proc = subprocess.Popen(
            ["git", "remote", "show", "origin"],
            stdout=subprocess.PIPE,
        )
        output = proc.communicate()[0].decode("utf-8")
        match = re.search("HEAD branch: (.+?)\n", output)
        if match:
            return match.group(1)

        raise Exception("Unable to parse git response")

    @staticmethod
    def get_current_repo_name() -> str:
        proc = subprocess.Popen(["git", "config", "--get", "remote.origin.url"], stdout=subprocess.PIPE)
        return proc.communicate()[0].decode("utf-8")

    @staticmethod
    def get_current_patchset() -> str:
        proc = subprocess.Popen(["git", "rev-parse", "--verify", "HEAD"], stdout=subprocess.PIPE)
        return proc.communicate()[0].decode("utf-8")
