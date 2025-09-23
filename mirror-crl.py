import requests
import xml.etree.ElementTree as ET
import zipfile
import os
import sys
import argparse
import shutil
from io import BytesIO
from typing import Tuple

APP_ID = "hfnkpimlhhgieaddgfemjhofmfblmnib"
PARAMS = {
    'x': f'id={APP_ID}&v=&uc&acceptformat=crx3',
    'tag': 'force_full'
}
VERSION_URL=f"https://clients2.google.com/service/update2/crx?{requests.compat.urlencode(PARAMS)}"
XML_NAMESPACE = '{http://www.google.com/update2/response}'

def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)

def fetch(pathtocheck: str) -> Tuple[bytes, str, str]:
    response = requests.get(VERSION_URL)
    if response.status_code != 200:
        fail("Failed to get version url.")

    root = ET.fromstring(response.text)

    crx_url = ""
    version = ""

    for app in root.findall(f'{XML_NAMESPACE}app'):
        if app.get('appid') == APP_ID:
            update_check = app.find(f'{XML_NAMESPACE}updatecheck')
            crx_url = update_check.get('codebase')
            version = update_check.get('version')
            break

    if not crx_url or not version:
        fail("Could not parse crx info from xml.")

    if os.path.isdir(os.path.join(pathtocheck, version)):
        print("Already up to date.")
        sys.exit(0)

    response = requests.get(crx_url)
    if response.status_code != 200:
        fail("Request for CRX failed.")

    return response.content, crx_url, version

def clear_old_versions(path: str) -> None:
    subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d.isdigit()]

    if len(subdirs) <= 2:
        return
    
    subdirs.sort(key=int)

    for d in subdirs[:-2]:
        full_path = os.path.join(path, d)
        if full_path != "/": # useless check, but just in case :)
            shutil.rmtree(full_path)

def main():
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
    path = os.path.expanduser(args.path).rstrip('/')

    if not os.path.isdir(path) or "CertificateRevocation" not in path:
        fail("Output directory invalid.")

    crx_bytes, crx_url, version = fetch(path)

    version_path = os.path.join(path, version)
    os.makedirs(version_path)

    with zipfile.ZipFile(BytesIO(crx_bytes)) as zf:
        zf.extractall(version_path)

    clear_old_versions(path)

    print("Successfully updated CRLSets. Enjoy!")

if __name__ == "__main__":
    main()