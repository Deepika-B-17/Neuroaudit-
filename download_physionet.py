import os
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://physionet.org/files/auditory-eeg/1.0.0/WFDB_Files/Filtered_Data/"

OUTPUT_DIR = Path(
    r"C:\Users\DINESH\Downloads\neuro\research_data\physionet_auditory\WFDB_Files\Filtered_Data"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RECORDINGS = [
    "ex01_s01",
    "ex01_s02",
    "ex01_s03",
    "ex02_s01",
    "ex02_s02",
    "ex02_s03",
    "ex05",
    "ex06",
    "ex07",
    "ex08",
    "ex09",
    "ex10",
]

SUBJECTS = range(3, 21)

MAX_RETRIES = 5
TIMEOUT = 30
CHUNK_SIZE = 64 * 1024


def download_file(filename):
    destination = OUTPUT_DIR / filename

    # Existing non-empty file: keep it.
    if destination.exists() and destination.stat().st_size > 0:
        print(f"[SKIP] {filename}")
        return True

    url = BASE_URL + filename
    temp_file = destination.with_suffix(destination.suffix + ".part")

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            print(f"[DOWNLOAD] {filename} (attempt {attempt}/{MAX_RETRIES})")

            if temp_file.exists():
                temp_file.unlink()

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "NeuroAudit-Dataset-Downloader/1.0"
                }
            )

            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                total_size = response.headers.get("Content-Length")

                if total_size:
                    total_size = int(total_size)
                    print(f"         Expected size: {total_size:,} bytes")

                downloaded = 0

                with open(temp_file, "wb") as f:
                    while True:
                        chunk = response.read(CHUNK_SIZE)

                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size:
                            percent = downloaded * 100 / total_size
                            print(
                                f"\r         {downloaded:,}/{total_size:,} "
                                f"({percent:.1f}%)",
                                end="",
                                flush=True
                            )
                        else:
                            print(
                                f"\r         {downloaded:,} bytes",
                                end="",
                                flush=True
                            )

                print()

            # Verify Content-Length if available.
            actual_size = temp_file.stat().st_size

            if total_size and actual_size != total_size:
                raise RuntimeError(
                    f"incomplete download: got {actual_size} "
                    f"out of {total_size} bytes"
                )

            temp_file.replace(destination)

            print(f"[OK] {filename}")
            return True

        except Exception as e:

            print()
            print(f"[ERROR] {filename}: {e}")

            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

            if attempt < MAX_RETRIES:
                print("         Retrying in 3 seconds...")
                time.sleep(3)

    print(f"[FAILED] {filename}")
    return False


def main():

    print("=" * 70)
    print("NeuroAudit PhysioNet Resume-Safe Downloader")
    print("=" * 70)
    print()
    print(f"Destination:")
    print(OUTPUT_DIR)
    print()
    print("Subjects: s03-s20")
    print("Existing files will be skipped.")
    print()

    failed = []

    for subject_number in SUBJECTS:

        subject = f"s{subject_number:02d}"

        print()
        print("-" * 70)
        print(f"SUBJECT {subject}")
        print("-" * 70)

        for recording in RECORDINGS:

            record_name = f"{subject}_{recording}"

            for extension in [".dat", ".hea"]:

                filename = record_name + extension

                if not download_file(filename):
                    failed.append(filename)

    print()
    print("=" * 70)
    print("DOWNLOAD RUN FINISHED")
    print("=" * 70)

    dat_count = len(list(OUTPUT_DIR.glob("*.dat")))
    hea_count = len(list(OUTPUT_DIR.glob("*.hea")))

    print(f".dat files currently present: {dat_count}")
    print(f".hea files currently present: {hea_count}")
    print(f"Total WFDB files: {dat_count + hea_count}")

    if failed:
        print()
        print("FAILED FILES:")
        for filename in failed:
            print(f"  {filename}")
    else:
        print()
        print("No failed downloads reported.")


if __name__ == "__main__":
    main()
