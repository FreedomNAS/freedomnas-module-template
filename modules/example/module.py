"""
ExampleModule — copy this file (and the rest of this repo) to create a new
module. Rename the class, update the docstring, and implement the three
FreedomNASModule methods below.

The Golden Rule (see freedomnas-core's ARCHITECTURE.md): never hardcode an
OS-native command in Python. Always go through self._engine.execute()/
get_command()/get_profile_value(), which resolve the right command from
this module's profile fragment (profiles/example/example-<os>.json in this
repo) — that's what makes the same module work unmodified on Debian,
FreeBSD, and Arch.
"""

from __future__ import annotations

import logging

# The try/except fallback matches freedomnas-core's own modules: it lets you
# test this file against a sibling freedomnas-core checkout's bare engine.py/
# config.py/orchestrator.py (see README.md "Local testing before packaging")
# without installing anything. A real install always has freedomnas-core
# installed as a proper package, so the first branch is what actually runs
# in production.
try:
    from freedomnas.engine import FreedomNASEngine, CommandExecutionError, CommandTranslationError
    from freedomnas.config import ConfigurationManager
    from freedomnas.orchestrator import FreedomNASModule
except ImportError:
    from engine import FreedomNASEngine, CommandExecutionError, CommandTranslationError  # type: ignore[no-redef]
    from config import ConfigurationManager  # type: ignore[no-redef]
    from orchestrator import FreedomNASModule  # type: ignore[no-redef]

# Match the logger name to the module id (see manifest.json's "id").
logger = logging.getLogger("FreedomNAS.Module.Example")


class ExampleModule(FreedomNASModule):
    """One-line description of what this module manages."""

    def __init__(self, engine: FreedomNASEngine, config: ConfigurationManager):
        super().__init__(engine, config)
        # Any state the module needs to track between start()/health_check()
        # calls goes here (see freedomnas-core's StorageModule._known_pools
        # for an example).

    @property
    def name(self) -> str:
        # Must match manifest.json's "id" and the profiles/<id>/ directory name.
        return "example"

    def start(self) -> None:
        """
        Called once by the Orchestrator when the module is (re)started.
        Must be idempotent — safe to call again after a restart.

        Typical uses: read expected state from self._config (e.g.
        self._config.get_pools(), self._config.get_users()) into instance
        state that health_check() will later verify against reality.
        """
        logger.info("ExampleModule started")

    def stop(self) -> None:
        """Called by the Orchestrator on shutdown. Must be idempotent."""
        logger.info("ExampleModule stopped")

    def health_check(self) -> bool:
        """
        Called every ~30s by the Orchestrator's heartbeat thread. Must never
        raise — catch everything internally and return False on failure.
        After 5 consecutive False results the Orchestrator's circuit breaker
        disables the module (see freedomnas-core's orchestrator.py MAX_FAILURES).

        Example: run a read-only command through the engine and check its
        output. Replace "category"/"action" with real entries from your
        profiles/example/example-<os>.json fragment.
        """
        try:
            self._engine.execute("category", "action")
        except (CommandExecutionError, CommandTranslationError) as exc:
            logger.warning("ExampleModule health_check failed: %s", exc)
            return False

        return True
