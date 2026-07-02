from __future__ import annotations

import json
import re
import time
import zipfile
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd
import requests

from .config import DATA_PAGE_URL, FORCES, KEEP_COLUMNS, MONTHS, RAW_DIR


CSV_RE = re.compile(
    r"(?P<month>\d{4}-\d{2})-(?P<force>.+)-(?P<kind>street|outcomes|stop-and-search)\.csv$",
    re.IGNORECASE,
)


def _extract_csrf_token(html: str) -> str:
    match = re.search(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)['\"]", html)
    if not match:
        match = re.search(r"value=['\"]([^'\"]+)['\"]\s+name=['\"]csrfmiddlewaretoken['\"]", html)
    if not match:
        raise RuntimeError("Could not find csrfmiddlewaretoken on data.police.uk/data/")
    return unescape(match.group(1))


def _zip_link_from_html(html: str, base_url: str) -> str | None:
    hrefs = re.findall(r"href=['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE)
    for href in hrefs:
        if ".zip" in href.lower():
            return urljoin(base_url, href)
    return None


def _progress_url_from_fetch_page(html: str, base_url: str) -> str | None:
    match = re.search(
        r'<script id="download-config" type="application/json">\s*\{\s*"url"\s*:\s*"([^"]+)"\s*\}\s*</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return urljoin(base_url, match.group(1))


def request_custom_download(
    date_from: str,
    date_to: str,
    forces: Iterable[str],
    include_outcomes: bool = False,
    session: requests.Session | None = None,
) -> str:
    """Ask data.police.uk to generate a custom CSV ZIP and return its fetch URL."""
    session = session or requests.Session()
    page = session.get(DATA_PAGE_URL, timeout=60)
    page.raise_for_status()
    token = _extract_csrf_token(page.text)

    data: list[tuple[str, str]] = [
        ("csrfmiddlewaretoken", token),
        ("date_from", date_from),
        ("date_to", date_to),
        ("include_crime", "on"),
    ]
    if include_outcomes:
        data.append(("include_outcomes", "on"))
    for force in forces:
        data.append(("forces", force))

    response = session.post(
        DATA_PAGE_URL,
        data=data,
        headers={"Referer": DATA_PAGE_URL},
        timeout=120,
        allow_redirects=False,
    )
    if response.status_code not in {302, 303}:
        response.raise_for_status()
        raise RuntimeError("Custom download request did not return a fetch redirect.")

    location = response.headers.get("location")
    if not location:
        raise RuntimeError("Custom download response did not include a Location header.")
    return urljoin(DATA_PAGE_URL, location)


def poll_and_download_zip(
    fetch_url: str,
    destination: Path,
    max_wait_seconds: int = 1800,
    poll_seconds: int = 20,
    session: requests.Session | None = None,
) -> Path:
    """Poll a generated data.police.uk fetch URL until the ZIP is ready."""
    session = session or requests.Session()
    destination.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()

    while True:
        response = session.get(fetch_url, timeout=120, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()

        if "zip" in content_type:
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            return destination

        html = response.text
        progress_url = _progress_url_from_fetch_page(html, fetch_url)
        if progress_url:
            progress = session.get(progress_url, timeout=60)
            progress.raise_for_status()
            status = progress.json()
            if status.get("status") == "ready" and status.get("url"):
                with session.get(status["url"], timeout=120, stream=True) as zip_response:
                    zip_response.raise_for_status()
                    with destination.open("wb") as f:
                        for chunk in zip_response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                return destination
            if status.get("status") == "error":
                raise RuntimeError(f"data.police.uk reported an error for {fetch_url}")

        zip_url = _zip_link_from_html(html, fetch_url)
        if zip_url:
            with session.get(zip_url, timeout=120, stream=True) as zip_response:
                zip_response.raise_for_status()
                with destination.open("wb") as f:
                    for chunk in zip_response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return destination

        if time.time() - started > max_wait_seconds:
            raise TimeoutError(
                f"Download was still generating after {max_wait_seconds} seconds: {fetch_url}"
            )
        time.sleep(poll_seconds)


def download_police_data(
    raw_dir: Path = RAW_DIR,
    months: list[str] | None = None,
    forces: dict[str, str] | None = None,
    force_download: bool = False,
    max_wait_seconds: int = 1800,
) -> Path:
    """Generate and download the custom police data ZIP if it is not already present."""
    months = months or MONTHS
    forces = forces or FORCES
    raw_dir.mkdir(parents=True, exist_ok=True)

    stem = f"police_custom_{months[0]}_{months[-1]}_{'_'.join(sorted(forces))}_street"
    zip_path = raw_dir / f"{stem}.zip"
    metadata_path = raw_dir / f"{stem}.json"

    if zip_path.exists() and zip_path.stat().st_size > 0 and not force_download:
        return zip_path

    session = requests.Session()
    fetch_url = request_custom_download(
        date_from=months[0],
        date_to=months[-1],
        forces=forces.keys(),
        include_outcomes=False,
        session=session,
    )
    metadata_path.write_text(
        json.dumps(
            {
                "data_page": DATA_PAGE_URL,
                "fetch_url": fetch_url,
                "date_from": months[0],
                "date_to": months[-1],
                "forces": forces,
                "include_crime": True,
                "include_outcomes": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return poll_and_download_zip(
        fetch_url=fetch_url,
        destination=zip_path,
        max_wait_seconds=max_wait_seconds,
        session=session,
    )


def parse_police_csv_name(name: str) -> dict[str, str] | None:
    basename = Path(name).name
    match = CSV_RE.search(basename)
    if not match:
        return None
    return match.groupdict()


def _normalise_column_name(column: str) -> str:
    column = column.strip().lower()
    column = re.sub(r"[^a-z0-9]+", "_", column)
    return column.strip("_")


def _standardise_frame(df: pd.DataFrame, force_slug: str, month: str, source_file: str) -> pd.DataFrame:
    df = df.rename(columns={col: _normalise_column_name(col) for col in df.columns})
    rename_map = {
        "crime_id": "crime_id",
        "crime_type": "crime_type",
        "last_outcome_category": "outcome_category",
        "outcome_category": "outcome_category",
        "outcome_type": "outcome_category",
        "lsoa_code": "lsoa_code",
        "lsoa_name": "lsoa_name",
        "latitude": "latitude",
        "longitude": "longitude",
        "month": "month",
    }
    df = df.rename(columns={old: new for old, new in rename_map.items() if old in df.columns})

    for col in KEEP_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df["force_slug"] = force_slug
    df["force"] = FORCES.get(force_slug, force_slug)
    if "month" not in df.columns or df["month"].isna().all():
        df["month"] = month
    else:
        df["month"] = df["month"].fillna(month)
    df["source_file"] = source_file

    df = df[KEEP_COLUMNS].copy()
    for col in df.columns:
        df[col] = df[col].astype("string")
        df[col] = df[col].str.strip()
        df.loc[df[col].isin(["", "nan", "None", "NULL", "null"]), col] = pd.NA
    return df


def _read_csv_from_zip(zip_path: Path, member: str, info: dict[str, str]) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member) as f:
            df = pd.read_csv(f, dtype="string", low_memory=False)
    return _standardise_frame(
        df=df,
        force_slug=info["force"],
        month=info["month"],
        source_file=f"{zip_path.name}:{member}",
    )


def _read_csv_file(path: Path, info: dict[str, str]) -> pd.DataFrame:
    df = pd.read_csv(path, dtype="string", low_memory=False)
    return _standardise_frame(
        df=df,
        force_slug=info["force"],
        month=info["month"],
        source_file=str(path),
    )


def load_force_data(
    raw_dir: Path = RAW_DIR,
    months: Iterable[str] | None = None,
    forces: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Load selected street-level police CSVs from ZIPs or extracted CSV files."""
    months = set(months or MONTHS)
    forces = set(forces or FORCES.keys())
    frames: list[pd.DataFrame] = []

    for zip_path in sorted(raw_dir.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                info = parse_police_csv_name(member)
                if not info:
                    continue
                if info["kind"].lower() != "street":
                    continue
                if info["month"] in months and info["force"] in forces:
                    frames.append(_read_csv_from_zip(zip_path, member, info))

    for csv_path in sorted(raw_dir.rglob("*.csv")):
        info = parse_police_csv_name(csv_path.name)
        if not info:
            continue
        if info["kind"].lower() != "street":
            continue
        if info["month"] in months and info["force"] in forces:
            frames.append(_read_csv_file(csv_path, info))

    if not frames:
        return pd.DataFrame(columns=KEEP_COLUMNS)

    data = pd.concat(frames, ignore_index=True)
    data = data.dropna(subset=["crime_type"]).copy()
    return data


def clean_police_data(data: pd.DataFrame) -> pd.DataFrame:
    """Clean the loaded street-level data for audit and network construction."""
    cleaned = data.copy()
    cleaned["crime_type"] = cleaned["crime_type"].str.strip()
    cleaned["outcome_category"] = cleaned["outcome_category"].str.strip()
    cleaned["lsoa_code"] = cleaned["lsoa_code"].str.strip()
    cleaned["lsoa_name"] = cleaned["lsoa_name"].str.strip()
    cleaned = cleaned.dropna(subset=["crime_type"]).copy()

    cleaned["area_id"] = cleaned["lsoa_code"]
    cleaned.loc[cleaned["area_id"].isna(), "area_id"] = cleaned.loc[
        cleaned["area_id"].isna(), "lsoa_name"
    ]
    cleaned["area_label"] = cleaned["lsoa_name"].fillna(cleaned["lsoa_code"])
    return cleaned
