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
        self.assertNotIn("GK" + "MediaRandomizer", readme)

    def test_installer_build_outputs_driftway_named_installer(self):
        installer = (ROOT / "Windows" / "installer.iss").read_text(encoding="utf-8")
        build = (ROOT / "Windows" / "build.bat").read_text(encoding="utf-8")
        spec = (ROOT / "Windows" / "DriftwayMediaRandomizer.spec").read_text(encoding="utf-8")

        self.assertIn('#define MyAppName "Driftway Media Randomizer"', installer)
        self.assertIn('#define MyAppExeName "DriftwayMediaRandomizer.exe"', installer)
        self.assertIn("OutputBaseFilename=Driftway_Media_Randomizer_Setup", installer)
        self.assertIn("dist\\DriftwayMediaRandomizer\\*", installer)
        self.assertIn("Driftway_Media_Randomizer_Setup.exe", build)
        self.assertIn("name='DriftwayMediaRandomizer'", spec)
        self.assertNotIn("GK" + "MediaRandomizer_Setup", installer + build)
        self.assertNotIn("GK" + "MediaRandomizer.spec", build)

    def test_assisted_update_relaunches_new_executable_after_rename(self):
        source = (ROOT / "Windows" / "gkmedia_randomizer.py").read_text(encoding="utf-8")
        installer = (ROOT / "Windows" / "installer.iss").read_text(encoding="utf-8")

        self.assertIn('target_app_exe = os.path.join(os.path.dirname(sys.executable), f"{APP_INTERNAL_NAME}.exe")', source)
        self.assertIn("Relaunching: {target_app_exe}", source)
        self.assertNotIn("Relaunching: {app_exe}", source)
        self.assertIn('[InstallDelete]', installer)
        self.assertIn('Name: "{app}\\*MediaRandomizer.exe"', installer)

    def test_user_visible_branding_uses_driftway_name(self):
        files = [
            ROOT / "Windows" / "gkmedia_randomizer.py",
            ROOT / "Windows" / "installer.iss",
            ROOT / "Windows" / "build.bat",
            ROOT / "Windows" / "assets" / "license.txt",
            ROOT / "Windows" / "assets" / "THIRD_PARTY_NOTICES.txt",
            ROOT / "LICENSE",
            ROOT / "CONTRIBUTING.md",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)

        self.assertIn("Driftway Media Randomizer", text)
        self.assertNotIn("GK" + "MediaRandomizer", text)

    def test_legacy_branding_is_removed_from_project_metadata(self):
        old_brand = "GK" + "MediaRandomizer"
        files = [
            ROOT / "CLAUDE.md",
            ROOT / "Package.swift",
            ROOT / "Sources" / "DriftwayMediaRandomizer" / "DriftwayMediaRandomizerApp.swift",
        ]
        missing = [str(path) for path in files if not path.exists()]
        self.assertEqual([], missing)
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        repo_paths = [path.as_posix() for path in ROOT.rglob("*") if ".git" not in path.parts]

        self.assertNotIn(old_brand, text)
        self.assertFalse(any(old_brand in path for path in repo_paths))


if __name__ == "__main__":
    unittest.main()
