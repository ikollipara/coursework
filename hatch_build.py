"""
hatch_build.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-09

Hatch build hook
"""

import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        path = Path(self.metadata.root) / "src" / "coursework_c"
        files = ((path / "coursework_admin.c", "coursework-admin"), (path / "coursework.c", "coursework"))

        for file, executable in files:
            result = subprocess.run(["gcc", file, "-o", f"{self.directory}/{executable}"])
            if result.returncode != 0:
                self.app.display_error(result.stderr)
                self.app.display_error(f"{file.name} failed to compile")
            else:
                self.app.display_success(f"{file} was successfully compiled")
        return super().initialize(version, build_data)
