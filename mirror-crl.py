import requests
import xml.etree.ElementTree as ET
import zipfile
import sys
import argparse
import shutil
from io import BytesIO
from typing import Tuple
from pathlib import Path

APP_ID = "hfnkpimlhhgieaddgfemjhofmfblmnib"
PARAMS = {
    "x": f"id={APP_ID}&v=&uc&acceptformat=crx3",
    "tag": "force_full"
}
VERSION_URL = f"https://clients2.google.com/service/update2/crx?{requests.compat.urlencode(PARAMS)}"
XML_NAMESPACE = "{http://www.google.com/update2/response}"

def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)

def get(url: str) -> requests.Response:
    try:
        return requests.get(url, timeout=10)
    except Exception as e:
        fail(f"Network error during get request for {url}")

def fetch(path_to_check: Path) -> Tuple[bytes, Path]:
    response = get(VERSION_URL)
    if response.status_code != 200:
        fail("Failed to get version url.")

    root = ET.fromstring(response.text)

    crx_url = ""
    version = ""

    for app in root.findall(f"{XML_NAMESPACE}app"):
        if app.get("appid") == APP_ID:
            update_check = app.find(f"{XML_NAMESPACE}updatecheck")
            crx_url = update_check.get("codebase")
            version = update_check.get("version")
            break

    if not crx_url or not version:
        fail("Could not parse crx info from xml.")

    version_path = path_to_check / version
    if version_path.is_dir():
        print("Already up to date.")
        sys.exit(0)

    response = get(crx_url)
    if response.status_code != 200:
        fail("Request for CRX failed.")

    crx_bytes = response.content
    if not crx_bytes.startswith(b"Cr24"):
        fail("CRX format from google has changed. Please file a github issue if the latest update still gets this error.")

    return crx_bytes, version_path

def clear_old_versions(path: Path) -> None:
    subdirs = sorted([d for d in path.iterdir() if d.is_dir() and d.name.isdigit()],
                  key=lambda d: int(d.name))

    if len(subdirs) <= 2:
        return

    for old in subdirs[:-2]:
        shutil.rmtree(old)

def extract_crx(crx_bytes: bytes, version_path: Path) -> None:
    version_path.mkdir(exist_ok=False)

    # Skip the header. Seems to not matter for now,
    # but in case google changes the header best to include this.
    zip_from_crx = crx_bytes[16:]

    with zipfile.ZipFile(BytesIO(zip_from_crx)) as zf:
        zf.extractall(version_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="""
    This will download the latest CRLSet component from google and extract it to the specified folder. 
    Intended for use in ungoogled chromium keeping this component up to date for those who want it.
    """)

    parser.add_argument(
        "--path",
        type=str,
        default="",
        help="""The CertificateRevocation directory to extract the CRLSet.
        The location of this varies. On my flatpak installation it is located here:
        "~/.var/app/io.github.ungoogled_software.ungoogled_chromium/config/chromium/CertificateRevocation".
        Please note, this can clean up existing old CRLSets in this directory, so don't do anything stupid like putting
        anything you care about in the CRLSet folders."""
    )

    args = parser.parse_args()
    path = Path(args.path).expanduser().resolve()

    if not path.is_dir() or path.name != "CertificateRevocation":
        fail("Output directory invalid.")

    crx_bytes, version_path = fetch(path)

    extract_crx(crx_bytes, version_path)

    clear_old_versions(path)

    print("Successfully updated CRLSets. Enjoy!")

if __name__ == "__main__":
    main()