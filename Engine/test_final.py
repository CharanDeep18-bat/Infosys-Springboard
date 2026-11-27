import sys
import shutil
import subprocess
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
FRONTEND = ENGINE.parent / "Frontend"
import os

os.environ["PYTHONPATH"] = (
    str(ENGINE)
    + os.pathsep
    + os.environ.get("PYTHONPATH", "")
)
results = []
test_files = [
    "tests/test_doc_owner.py",
    "test_data_isolation.py",
    "test_ageent_auth.py",
    "test_chunk_ownership.py",
    "test_vector_isolation.py",
    "test_research_security.py",
    "test_search_security.py",
    "test_vector_agent_arch.py",
    "test_reindex_security.py",
    "test_processing_api.py",
    "test_document_deletion.py",
    "test_session_management.py",
    "test_session_features.py",
    "test_final_config.py",
    "test_final_bugs.py",
    "test_frontend_isolation.py",
    "test_report_agent.py",
"test_pdf_export.py",
"test_report_frontend.py",
"test_automatic_processing.py",
"test_seed_documents.py",
"test_live_integration.py",
]
def run_check(name, command, cwd):

    print("\n" + "=" * 65)
    print(name)
    print("=" * 65)

    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            timeout=300
        )

        status = "PASS" if result.returncode == 0 else "FAIL"

    except subprocess.TimeoutExpired:
        status = "TIMEOUT"

    except Exception as exc:
        print(exc)
        status = "FAIL"

    results.append((name, status))


run_check(
    "Backend Python syntax",
    [sys.executable, "-m", "compileall", "-q", "app"],
    ENGINE
)


for filename in test_files:

    if not (ENGINE / filename).exists():
        results.append((filename, "MISSING"))
        continue

    run_check(
        filename,
        [sys.executable, filename],
        ENGINE
    )


npm = shutil.which("npm.cmd") or shutil.which("npm")

if npm and FRONTEND.exists():

    run_check(
        "Frontend production build",
        [npm, "run", "build"],
        FRONTEND
    )

else:
    results.append(
        ("Frontend production build", "MISSING")
    )


print("\n" + "=" * 65)
print("FINAL PROJECT TEST REPORT")
print("=" * 65)

for name, status in results:
    print(f"{name:<45} {status:>10}")

passed = sum(
    status == "PASS" for _, status in results
)

failed = sum(
    status == "FAIL" for _, status in results
)

missing = sum(
    status == "MISSING" for _, status in results
)

timeouts = sum(
    status == "TIMEOUT" for _, status in results
)

print("-" * 65)
print(f"Total checks : {len(results)}")
print(f"Passed       : {passed}")
print(f"Failed       : {failed}")
print(f"Missing      : {missing}")
print(f"Timeouts     : {timeouts}")
print("-" * 65)

if passed == len(results):
    print("ALL CONFIGURED CHECKS PASSED")
    sys.exit(0)
else:
    print("PROJECT REQUIRES ADDITIONAL FIXES")
    sys.exit(1)