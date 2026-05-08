import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_constants():
    source = (ROOT / "Windows" / "gkmedia_randomizer.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    constants = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {"REPO_OWNER", "REPO_NAME"}:
                constants[target.id] = ast.literal_eval(node.value)
    return constants, source


class RepoMetadataTests(unittest.TestCase):
    def test_update_checker_uses_primary_repository_releases(self):
        constants, source = _read_constants()

        self.assertEqual(constants["REPO_OWNER"], "karagioules")
        self.assertEqual(constants["REPO_NAME"], "Driftway_Media_Randomizer")
        self.assertIn("/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest", source)

    def test_readme_uses_driftway_name_and_mylocalbackup_hero_system(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("<div align=\"center\">", readme)
        self.assertIn("<h1>Driftway Media Randomizer</h1>", readme)
        self.assertIn("releases/latest", readme)
        self.assertIn("&bull;", readme)
        self.assertNotIn("GKMediaRandomizer", readme)


if __name__ == "__main__":
    unittest.main()
