import logging
import subprocess
from typing import List


class CmdException(Exception):
    """Exception raised for errors in the command line."""


def run_command_factory(exception_type: Exception):
    """Returns a subprocess run command that captures stdout and stderr and forwards stdin."""

    def inner(command: List[str], logger: logging.Logger = None):
        """Run a command in the shell, stream std output."""
        command_str = " ".join(command)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output_lines, error_lines = [], []

        # Stream output coming from the process realtime.
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            if error:
                error_lines.append(error.strip())
            if output == "" and process.poll() is not None:
                break
            if output:
                output_lines.append(output.strip())
                if logger:
                    logger.info(output.strip())

        # Capture any remaining output from stderr.
        for line in process.stderr.readlines():
            error_lines.append(line.strip())

        rc = process.poll()
        if rc != 0:
            msg = "\n".join(error_lines)
            exceptionMsg = f"issue with running {command_str}: {msg}"
            raise exception_type(exceptionMsg)
        return "\n".join(output_lines)

    return inner
