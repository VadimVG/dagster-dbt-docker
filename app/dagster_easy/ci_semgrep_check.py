# Temporary file to check that the CI semgrep job fails. Delete it after the test.
import subprocess


def run(cmd):
    return subprocess.run(cmd, shell=True)
