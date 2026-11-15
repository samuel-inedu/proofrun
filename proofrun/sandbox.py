"""Run shell commands in a work folder, on this machine or in a Docker container."""
import os
import subprocess
import sys


class CommandResult:
    def __init__(self, code, output, timed_out=False):
        self.code = code
        self.output = output
        self.timed_out = timed_out

    @property
    def ok(self):
        return self.code == 0 and not self.timed_out


def local_command(command, windows=None):
    """On Windows the program name is 'python', not 'python3'. Use the Python that runs the harness."""
    windows = os.name == "nt" if windows is None else windows
    if windows and command.startswith("python3 "):
        return f'"{sys.executable}"' + command[len("python3"):]
    return command


def run(command, workdir, backend="local", image=None, timeout=300):
    """Run one shell command. Exit code 0 means success."""
    if backend == "docker":
        if not image:
            raise ValueError("the docker backend needs an image (set 'image' in the task)")
        argv = [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{workdir}:/work", "-w", "/work",
            image, "sh", "-c", command,
        ]
        shell = False
    elif backend == "local":
        argv = local_command(command)
        shell = True
    else:
        raise ValueError(f"unknown backend: {backend}")
    try:
        done = subprocess.run(
            argv, shell=shell, cwd=workdir, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
        )
    except subprocess.TimeoutExpired as error:
        partial = error.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        return CommandResult(-1, partial, timed_out=True)
    return CommandResult(done.returncode, done.stdout)


def docker_ready():
    """Return (ok, message). Call this before a run with the docker backend."""
    try:
        done = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, errors="replace", timeout=30)
    except FileNotFoundError:
        return False, "the docker program is not installed"
    except subprocess.TimeoutExpired:
        return False, "docker did not answer in 30 seconds"
    if done.returncode != 0:
        return False, done.stdout.strip().splitlines()[-1] if done.stdout.strip() else "docker info failed"
    return True, "docker is ready"
