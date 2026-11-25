"""End-to-End Verification of Milestone 2 Multi-Agent Orchestration.

Tests the sequential pipeline:
Document Agent -> Extraction Agent -> Evidence Validation -> Red Flag Agent -> Persistence
across seed company financial documents.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.database import get_database_repository
from app.orchestration.workflow import MultiAgentWorkflowOrchestrator


def main():
    repo = get_database_repository()
    docs = repo.list_documents()
    print(f"Total documents registered in database: {len(docs)}")

    tested_count = 0
    passed_count = 0

    for doc in docs:
        doc_id = doc["document_id"]
        filename = doc.get("filename", "unknown.pdf")
        print(f"\n=======================================================")
        print(f"Processing: {filename} (ID: {doc_id})")
        print(f"=======================================================")

        state = MultiAgentWorkflowOrchestrator.run_pipeline(
            document_id=doc_id,
            filename=filename,
            workspace_id="default-workspace",
        )

        tested_count += 1
        print(f"Pipeline Result:")
        print(f" - Final Phase:        {state.current_phase}")
        print(f" - Execution Failed:    {state.is_failed}")
        print(f" - Total Pages:         {state.total_pages}")
        print(f" - Total Chunks:        {state.chunk_count}")
        print(f" - Metrics Extracted:   {state.extracted_metrics_count}")
        print(f" - Validation Passed:   {state.validation_passed}")
        print(f" - Red Flags Found:     {state.red_flag_count}")

        if state.red_flag_findings:
            print(" - Sample Red Flags:")
            for rf in state.red_flag_findings[:2]:
                print(f"    * [{rf['severity']}] {rf['title']} (Page {rf.get('source_page', '?')})")

        # Verify database persistence
        metrics = repo.get_financial_metrics(doc_id)
        red_flags = repo.get_red_flag_findings(doc_id)
        runs = repo.get_agent_runs(doc_id)

        print(f"Database Persistence Check:")
        print(f" - Persisted Metrics:   {len(metrics)}")
        print(f" - Persisted Red Flags: {len(red_flags)}")
        print(f" - Agent Runs Logged:   {len(runs)}")

        if not state.is_failed and len(metrics) > 0:
            passed_count += 1
            print(">>> STATUS: PASSED")
        else:
            print(f">>> STATUS: FAILED / ERRORS: {state.errors}")

    print(f"\n=======================================================")
    print(f"Milestone 2 Verification Complete: {passed_count}/{tested_count} Documents Successfully Processed")
    print(f"=======================================================")


if __name__ == "__main__":
    main()

