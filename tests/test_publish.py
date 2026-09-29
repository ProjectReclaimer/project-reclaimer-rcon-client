import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("publish", Path(__file__).parents[1] / "scripts/publish.py")
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


class PublishingSafeguards(unittest.TestCase):
    def test_tag_cannot_escape_the_asset_name(self):
        for tag in ["../main", "v1.2.3/../../source", "v1.2.3\nmain", "main"]:
            with self.assertRaises(ValueError):
                publish.executable_name(tag)
        self.assertEqual(publish.executable_name("v1.2.3-beta.1"), "reclaimer-rcon-v1.2.3-beta.1.exe")

    def test_only_expected_executable_can_be_verified(self):
        name = publish.executable_name("v1.2.3")
        binary = b"MZtest executable"
        digest = hashlib.sha256(binary).hexdigest()
        with tempfile.TemporaryDirectory() as staging:
            directory = Path(staging)
            (directory / name).write_bytes(binary)
            manifest = directory / "RCON-SHA256SUMS.txt"
            manifest.write_text(f"{digest}  {name}\n")
            self.assertEqual(publish.verify(directory, name), f"{digest}  {name}\n")
            for content in [f"{digest}  ../source.rs\n", f"{digest}  {name}\n{digest}  secret.txt\n", f"{'0' * 64}  {name}\n"]:
                manifest.write_text(content)
                with self.assertRaises(ValueError):
                    publish.verify(directory, name)
            (directory / name).write_bytes(b"source code")
            manifest.write_text(f"{hashlib.sha256(b'source code').hexdigest()}  {name}\n")
            with self.assertRaises(ValueError):
                publish.verify(directory, name)


if __name__ == "__main__":
    unittest.main()
