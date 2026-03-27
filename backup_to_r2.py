from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
TMP_DIR = PROJECT_ROOT / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

if os.name == "nt":
    load_dotenv(PROJECT_ROOT / ".env.dev")
else:
    load_dotenv(PROJECT_ROOT / ".env.prod")

STAMP = time.strftime("%Y-%m-%d_%H-%M-%S")
MODE = os.getenv("ENVIRONMENT", "development").lower()

DB_DUMP_FILE = TMP_DIR / f"db_{STAMP}.dump"
ARCHIVE_FILE = TMP_DIR / f"backup_{MODE}_{STAMP}.tar.gz"

EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDE_TOP_LEVEL = {
    "tmp",
}

PROD_EXTRA_PATHS = [
    Path("/var/www/cargodb/staticfiles"),
    Path("/var/www/cargodb/media"),
    Path("/var/www/cargodb/translations"),
]


def format_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def format_speed(num_bytes: int, seconds: float) -> str:
    if seconds <= 0:
        return "n/a"
    return f"{format_size(int(num_bytes / seconds))}/s"


def should_skip(path: Path) -> bool:
    try:
        rel_parts = path.relative_to(PROJECT_ROOT).parts
    except ValueError:
        return False

    if not rel_parts:
        return False

    if rel_parts[0] in EXCLUDE_TOP_LEVEL:
        return True

    return any(part in EXCLUDE_DIRS for part in rel_parts)


def build_db_dump_cmd() -> tuple[list[str], dict[str, str]]:
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not db_name or not db_user or not db_password:
        raise RuntimeError("DB_NAME / DB_USER / DB_PASSWORD not found in env")

    if MODE == "development":
        db_container = os.getenv("DB_CONTAINER", "cargo_db")
        cmd = [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={db_password}",
            "-i",
            db_container,
            "pg_dump",
            "-U",
            db_user,
            "-Fc",
            db_name,
        ]
        return cmd, os.environ.copy()

    db_host = os.getenv("IP_POSTGRES")
    db_port = os.getenv("DB_PORT", "5432")

    if not db_host:
        raise RuntimeError("IP_POSTGRES not found in env")

    env = os.environ.copy()
    env["PGPASSWORD"] = db_password

    cmd = [
        "pg_dump",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-Fc",
        db_name,
    ]
    return cmd, env


def run_db_dump() -> tuple[Path, int, float]:
    start = time.perf_counter()
    cmd, env = build_db_dump_cmd()

    with DB_DUMP_FILE.open("wb") as fh:
        proc = subprocess.run(
            cmd,
            stdout=fh,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"pg_dump failed:\n{err}")

    size = DB_DUMP_FILE.stat().st_size
    if size <= 0:
        raise RuntimeError("pg_dump produced empty dump file")

    elapsed = time.perf_counter() - start
    return DB_DUMP_FILE, size, elapsed


def add_project_files(tar: tarfile.TarFile) -> int:
    added_files = 0

    for path in PROJECT_ROOT.rglob("*"):
        if should_skip(path):
            continue
        if not path.is_file():
            continue
        if path.resolve() in {ARCHIVE_FILE.resolve(), DB_DUMP_FILE.resolve()}:
            continue

        arcname = Path("project") / path.relative_to(PROJECT_ROOT)
        tar.add(path, arcname=str(arcname))
        added_files += 1

    return added_files


def add_prod_extra_files(tar: tarfile.TarFile) -> int:
    if MODE != "production":
        return 0

    added_files = 0

    for base_path in PROD_EXTRA_PATHS:
        if not base_path.exists():
            continue

        for path in base_path.rglob("*"):
            if not path.is_file():
                continue

            arcname = Path("server_data") / base_path.name / path.relative_to(base_path)
            tar.add(path, arcname=str(arcname))
            added_files += 1

    return added_files


def build_archive(db_dump_path: Path) -> tuple[int, float, int]:
    start = time.perf_counter()
    added_files = 0

    with tarfile.open(ARCHIVE_FILE, mode="w:gz") as tar:
        tar.add(db_dump_path, arcname=f"db/{db_dump_path.name}")
        added_files += 1

        added_files += add_project_files(tar)
        added_files += add_prod_extra_files(tar)

    elapsed = time.perf_counter() - start
    size = ARCHIVE_FILE.stat().st_size
    return size, elapsed, added_files


def upload_to_r2(file_path: Path) -> float:
    start = time.perf_counter()

    r2_endpoint = os.getenv("R2_ENDPOINT")
    r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    r2_bucket = os.getenv("R2_BUCKET_NAME")

    if not all([r2_endpoint, r2_access_key, r2_secret_key, r2_bucket]):
        raise RuntimeError("R2 credentials missing in env")

    s3 = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=r2_access_key,
        aws_secret_access_key=r2_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    s3.upload_file(str(file_path), r2_bucket, file_path.name)
    return time.perf_counter() - start


def main() -> int:
    print(f"MODE         : {MODE}")
    print(f"STAMP        : {STAMP}")
    print(f"PROJECT_ROOT : {PROJECT_ROOT}")
    print("-" * 30)

    print("[1/3] DB dump...")
    db_path, db_size, db_sec = run_db_dump()
    print(f"Done: {format_size(db_size)} in {db_sec:.2f}s ({format_speed(db_size, db_sec)})")

    print("\n[2/3] Creating archive...")
    arc_size, arc_sec, files_count = build_archive(db_path)
    print(f"Done: {files_count} files, {format_size(arc_size)} in {arc_sec:.2f}s")

    print("\n[3/3] Uploading to R2...")
    up_sec = upload_to_r2(ARCHIVE_FILE)
    print(f"Done: uploaded in {up_sec:.2f}s ({format_speed(arc_size, up_sec)})")

    print("\nCleaning up...")
    db_path.unlink(missing_ok=True)

    print("ALL DONE SUCCESSFULLY")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"\nCRITICAL ERROR: {exc}", file=sys.stderr)
        sys.exit(1)