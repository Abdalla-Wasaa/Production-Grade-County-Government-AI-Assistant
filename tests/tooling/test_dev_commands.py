"""Local credentials and reset boundaries; no Docker resources are touched."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "dev", Path(__file__).resolve().parents[2] / "scripts/dev.py"
)
dev = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dev)


class DevelopmentCommands(unittest.TestCase):
    def test_independent_private_credentials_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "new"
            environment, state = dev.generate_environment(directory, "county-dev", 8080)
            passwords = [
                (directory / "secrets" / (role + "_password")).read_text().strip()
                for role in ("bootstrap", "migration", "runtime")
            ]
            self.assertEqual(len(set(passwords)), 3)
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertTrue(state["disposable"])
            for value in passwords:
                self.assertNotIn(value, environment.read_text())
            with self.assertRaises(FileExistsError):
                dev.generate_environment(directory, "county-dev", 8080)
            self.assertEqual(
                passwords[0],
                (directory / "secrets/bootstrap_password").read_text().strip(),
            )

    def test_project_and_port_validation(self):
        for project, port in [
            ("coursework", 8080),
            ("county-dev", 80),
            ("../county-dev", 8080),
        ]:
            with self.subTest(project=project), self.assertRaises(ValueError):
                dev.generate_environment(Path("/unused"), project, port)

    def test_reset_refuses_missing_confirmation_before_docker(self):
        state = {"project": "county-dev", "instance": "example"}
        with (
            patch.object(dev, "load_local_state", return_value=state),
            patch.object(dev, "owned_resources") as resources,
        ):
            with self.assertRaises(ValueError):
                dev.reset("yes")
            resources.assert_not_called()

    def test_foreign_or_incomplete_labels_are_rejected(self):
        labels = {
            "com.docker.compose.project": "county-dev",
            dev.LABEL + "managed": "true",
            dev.LABEL + "disposable": "true",
            dev.LABEL + "instance": "own",
        }
        dev.verify_ownership([{"Labels": labels}], "county-dev", "own")
        for key in labels:
            foreign = dict(labels)
            foreign.pop(key)
            with self.assertRaises(ValueError):
                dev.verify_ownership([{"Labels": foreign}], "county-dev", "own")

    def test_reset_checks_ownership_before_any_removal(self):
        state = {"project": "county-dev", "instance": "own"}
        with (
            patch.object(dev, "load_local_state", return_value=state),
            patch.object(dev, "owned_resources", side_effect=ValueError("foreign")),
            patch.object(dev.subprocess, "run") as run,
        ):
            with self.assertRaises(ValueError):
                dev.reset("RESET county-dev")
            run.assert_not_called()

    def test_reset_targets_fixed_project_and_preserves_secret_files(self):
        state = {"project": "county-dev", "instance": "own"}
        with (
            patch.object(dev, "load_local_state", return_value=state),
            patch.object(dev, "owned_resources") as owned,
            patch.object(dev.subprocess, "run") as run,
        ):
            dev.reset("RESET county-dev")
            owned.assert_called_once_with("county-dev", "own")
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ["down", "--volumes"])
            self.assertIn("county-dev", command)
            self.assertNotIn("prune", command)

    def test_symlinked_local_parent_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            foreign = Path(tmp) / "foreign"
            root.mkdir()
            foreign.mkdir()
            (root / ".local").symlink_to(foreign, target_is_directory=True)
            with patch.object(dev, "ROOT", root), self.assertRaises(ValueError):
                dev.setup()
            self.assertEqual(list(foreign.iterdir()), [])

    def test_stopped_containers_are_included_in_ownership_check(self):
        from subprocess import CompletedProcess

        with patch.object(
            dev.subprocess, "run", return_value=CompletedProcess([], 0, stdout="")
        ) as run:
            dev.owned_resources("county-dev", "own")
            self.assertIn("--all", run.call_args_list[0].args[0])

    def test_alternate_compose_and_application_environment_is_removed(self):
        with patch.dict(
            os.environ,
            {"COMPOSE_FILE": "foreign.yml", "COUNTY_DATABASE_URL": "private"},
        ):
            environment = dev.docker_environment()
            self.assertNotIn("COMPOSE_FILE", environment)
            self.assertNotIn("COUNTY_DATABASE_URL", environment)
            self.assertEqual(environment["COMPOSE_BAKE"], "false")


if __name__ == "__main__":
    unittest.main()
