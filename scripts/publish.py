"""Mirror two explicitly allowed release assets from an already-public repository."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

SOURCE = "ProjectReclaimer/project-reclaimer-releases"
DESTINATION = "ProjectReclaimer/project-reclaimer-rcon-client"


def gh(*args, check=True):
    return subprocess.run(["gh", *args], text=True, capture_output=True, check=check)


def api(path):
    return json.loads(gh("api", path).stdout)


def executable_name(tag):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", tag):
        raise ValueError("Expected a version tag such as v0.8.10 or v0.8.10-beta.1")
    return f"reclaimer-rcon-{tag}.exe"


def verify(directory, name):
    """Never feed an untrusted manifest to a tool that follows its file paths."""
    lines = (directory / "RCON-SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    if len(lines) != 1:
        raise ValueError("Expected exactly one checksum entry")
    match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *]" + re.escape(name), lines[0])
    if not match:
        raise ValueError("Checksum must name only the expected RCON executable")
    binary = (directory / name).read_bytes()
    if not binary.startswith(b"MZ"):
        raise ValueError("Asset is not a Windows executable")
    digest = hashlib.sha256(binary).hexdigest()
    if digest != match[1].lower():
        raise ValueError("RCON executable failed SHA-256 verification")
    return f"{digest}  {name}\n"


def publish(release, latest):
    tag = release["tag_name"]
    name = executable_name(tag)
    assets = {asset["name"]: asset for asset in release["assets"]}
    expected = {name, "RCON-SHA256SUMS.txt"}
    if release["draft"] or not expected <= assets.keys():
        return False
    if assets[name]["size"] > 100 * 1024 * 1024 or assets["RCON-SHA256SUMS.txt"]["size"] > 1024:
        raise ValueError("Unexpected release asset size")
    existing = gh("api", f"repos/{DESTINATION}/releases/tags/{tag}", check=False)
    if existing.returncode == 0:
        published = json.loads(existing.stdout)
        published_assets = {asset["name"]: asset for asset in published["assets"]}
        digest = assets[name].get("digest")
        if (not published["draft"] and digest and "SHA256SUMS.txt" in published_assets
                and published_assets.get(name, {}).get("digest") == digest):
            print(f"{tag} is already published.")
            return True
    elif "HTTP 404" not in existing.stderr:
        raise RuntimeError(existing.stderr)
    with tempfile.TemporaryDirectory(prefix="rcon-release-") as staging:
        directory = Path(staging)
        # No wildcard copies, repository archives, source checkouts or PDB files.
        gh("release", "download", tag, "--repo", SOURCE, "--dir", staging,
           "--pattern", name, "--pattern", "RCON-SHA256SUMS.txt")
        checksum = directory / "SHA256SUMS.txt"
        checksum.write_text(verify(directory, name), encoding="utf-8", newline="\n")
        if existing.returncode != 0:
            notes = directory / "notes.md"
            notes.write_text(
                f"Download **{name}** below and double-click to run it.\n\n"
                "Standalone Windows desktop RCON client for Project Reclaimer dedicated servers. "
                "No game installation is required. Connect using the server's host, RCON port "
                "and password to manage players, send commands and watch live events.\n\n"
                f"[Connection guide](https://github.com/{DESTINATION}#connect). "
                "Verify the executable with the attached SHA256SUMS.txt.\n\n"
                "The automatic Source code archives contain only this download repository's "
                "documentation and publishing automation.\n", encoding="utf-8")
            flags = ["--prerelease"] if release["prerelease"] else []
            gh("release", "create", tag, "--repo", DESTINATION, "--target", "main",
               "--title", f"Reclaimer RCON {tag}", "--notes-file", str(notes), "--draft", *flags)
        gh("release", "upload", tag, "--repo", DESTINATION, "--clobber", str(directory / name), str(checksum))
        gh("release", "edit", tag, "--repo", DESTINATION, "--draft=false",
           f"--prerelease={'true' if release['prerelease'] else 'false'}",
           f"--latest={'true' if tag == latest and not release['prerelease'] else 'false'}")
        print(f"Published https://github.com/{DESTINATION}/releases/tag/{tag}")
    return True


def main():
    if os.environ.get("GITHUB_REPOSITORY", DESTINATION).lower() != DESTINATION.lower():
        raise ValueError("Publishing is restricted to the official RCON downloads repository")
    tag = os.environ.get("RELEASE_TAG", "").strip()
    if tag:
        executable_name(tag)
        releases = [api(f"repos/{SOURCE}/releases/tags/{tag}")]
    else:
        releases = list(reversed(api(f"repos/{SOURCE}/releases?per_page=100")))
    latest = api(f"repos/{SOURCE}/releases/latest")["tag_name"]
    for release in releases:
        if not publish(release, latest) and tag:
            raise ValueError(f"{tag} does not yet contain both RCON release assets")


if __name__ == "__main__":
    main()
