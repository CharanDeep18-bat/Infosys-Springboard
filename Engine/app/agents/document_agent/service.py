"""Document Intelligence Agent Service.

Core implementation for Milestone 1:
- PDF upload and validation
- Duplicate detection via SHA-256
- Text and financial table extraction
- Structure-aware chunking
- Embedding generation
- Qdrant/Chroma vector persistence
- Research workspace and session association
- Semantic document retrieval
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import get_settings
from app.infrastructure.database import (
    DatabaseRepositoryInterface,
    get_database_repository,
)
from app.infrastructure.document_processing import (
    DocumentParserInterface,
    PyMuPDFParser,
    StructureAwareChunker,
    generate_embeddings,
    get_embedding_dimension,
    get_embedding_provider,
)
from app.infrastructure.storage import FileStorageInterface, get_file_storage
from app.infrastructure.vector_store import (
    VectorStoreInterface,
    get_vector_store,
)
from app.schemas.document import DocumentSummary, DocumentUploadResponse, SeedDocumentResult
from app.schemas.search import SearchResponse, SearchResultItem

logger = logging.getLogger(__name__)


class DocumentAgentService:
    """Production service coordinating document ingestion, indexing, and search."""

    def __init__(
        self,
        repository: Optional[DatabaseRepositoryInterface] = None,
        storage: Optional[FileStorageInterface] = None,
        vector_store: Optional[VectorStoreInterface] = None,
        parser: Optional[DocumentParserInterface] = None,
        chunker: Optional[StructureAwareChunker] = None,
    ):
        self.settings = get_settings()
        self.repo = repository or get_database_repository()
        self.storage = storage or get_file_storage()
        self.vector_store = vector_store or get_vector_store()
        self.parser = parser or PyMuPDFParser()
        self.chunker = chunker or StructureAwareChunker()

    def process_pdf_upload(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        *,
        user_id: str,
    ) -> DocumentUploadResponse:
        """Validate, deduplicate, parse, chunk, embed, and index an uploaded PDF."""
        if not user_id:
            raise ValueError("Document owner is required")

        if document_id is not None:
            raise ValueError("Custom document IDs are not allowed")

        if not workspace_id:
            workspace = self.repo.get_or_create_default_workspace(
                user_id=user_id
            )
            workspace_id = workspace["workspace_id"]

        workspace = self.repo.get_user_workspace(
            workspace_id=workspace_id,
            user_id=user_id
        )

        if not workspace:
            raise ValueError("Workspace not found")

        if session_id:
            session = self.repo.get_user_session(
                session_id=session_id,
                user_id=user_id
            )

            if not session or session["workspace_id"] != workspace_id:
                raise ValueError("Session not found")
        # 1. Validation
        if not filename or not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        if not file_bytes:
            raise ValueError("The uploaded file is empty.")

        if len(file_bytes) > self.settings.max_file_size:
            max_mb = self.settings.max_file_size // (1024 * 1024)
            raise ValueError(f"File exceeds the {max_mb} MB limit.")

        # 2. User-specific SHA-256 Duplicate Check
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        existing_doc = self.repo.get_user_document_by_sha256(
            sha256_hash=file_hash,
            user_id=user_id
        )

        if existing_doc and existing_doc["workspace_id"] != workspace_id:
            raise ValueError(
                "This document already exists in another workspace"
            )

        if not document_id and existing_doc and existing_doc.get("indexed") == 1:
            doc_id = existing_doc["document_id"]
            # Ensure the vector store actually contains indexed chunks for this document
            existing_chunks = self.vector_store.get_chunks_by_document(
                doc_id,
                user_id=user_id,
                workspace_id=workspace_id
            )       
            if existing_chunks:
                if session_id:
                    self.repo.add_document_to_session(session_id, doc_id)

                return DocumentUploadResponse(
                    document_id=doc_id,
                    filename=filename,
                    total_pages=existing_doc.get("total_pages", 0),
                    characters_extracted=existing_doc.get("total_characters", 0),
                    text_preview="Document already indexed in system.",
                    stored=True,
                    indexed=True,
                    already_exists=True,
                    chunk_count=existing_doc.get("chunk_count", 0),
                    chunk_preview=[],
                    message="This document already exists and is indexed.",
                    session_id=session_id,
                )

        # 3. Document ID and File Storage
        document_id = (
            existing_doc["document_id"]
            if existing_doc
            else uuid4().hex
        )   
        stored_path = self.storage.save_file(file_bytes, filename, document_id)

        # 4. Parse PDF (Text + Tables)
        try:
            parsed_pages = self.parser.parse_pdf(file_bytes)
        except Exception as e:
            logger.error("Failed to parse PDF %s: %s", filename, e)
            raise ValueError(f"Unable to parse PDF: {e}") from e

        total_pages = len(parsed_pages)
        total_tables = sum(len(p.tables) for p in parsed_pages)
        full_text = "\n\n".join(p.text for p in parsed_pages if p.text).strip()
        total_chars = len(full_text)

        # 5. Structure-Aware & Token-Aware Chunking
        chunks = self.chunker.chunk_pages(parsed_pages, document_id, filename)
        for chunk in chunks:
            chunk["user_id"] = user_id
            chunk["workspace_id"] = workspace_id
        # 6. Register initial record before vector storage
        storage_provider = getattr(self.storage, "get_storage_provider", lambda: "local")()
        object_key = getattr(self.storage, "get_object_key", lambda doc_id: f"{doc_id}.pdf")(document_id)
        bucket_name = getattr(self.storage, "bucket_name", None)
        storage_path_val = (
            f"supabase://{bucket_name}/{object_key}"
            if storage_provider == "supabase"
            else str(stored_path)
        )

        doc_record = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "sha256": file_hash,
            "filename": filename,
            "stored_filename": object_key,
            "storage_path": storage_path_val,
            "total_pages": total_pages,
            "total_characters": total_chars,
            "chunk_count": len(chunks),
            "indexed": 0,
            "mime_type": "application/pdf",
            "metadata": {
                "tables_detected": total_tables,
                "sections": list({p.section for p in parsed_pages if p.section}),
                "storage_provider": storage_provider,
                "object_key": object_key,
                "bucket": bucket_name,
                "file_size_bytes": len(file_bytes),
                "embedding_provider": self.settings.embedding_provider,
                "embedding_model": getattr(
                    get_embedding_provider(),
                    "get_model_name",
                    lambda: self.settings.embedding_model,
                )(),
                "embedding_dimension": get_embedding_dimension(),
                "ocr_engine": "PyMuPDF High-Fidelity Extraction",
            },
        }
        self.repo.create_document(doc_record)

        if session_id:
            self.repo.add_document_to_session(session_id, document_id)

        # 7. Embedding Generation & Vector Indexing
        indexed_successfully = False
        if chunks:
            try:
                texts = [c["text"] for c in chunks]
                embeddings = generate_embeddings(texts)
                self.vector_store.upsert_chunks(chunks, embeddings)

                self.repo.update_document_indexed(
                    document_id=document_id,
                    indexed=1,
                    chunk_count=len(chunks),
                    total_pages=total_pages,
                    total_characters=total_chars,
                    metadata=doc_record["metadata"],
                )
                indexed_successfully = True
            except Exception as e:
                logger.exception("Failed to index document %s into vector store: %s", document_id, e)
                raise RuntimeError(f"Document saved, but vector indexing failed: {e}") from e

        # 8. Construct Response Message
        if indexed_successfully:
            msg = f"PDF processed successfully. {total_pages} pages, {total_tables} financial tables, {len(chunks)} chunks indexed."
        elif not full_text:
            msg = "PDF saved, but no selectable text was found. Scanned PDFs may require OCR."
        else:
            msg = "PDF saved, but no chunks were generated. Document is not indexed."

        chunk_previews = [
            {
                "page_number": c["page_number"],
                "is_table": c.get("is_table", False),
                "text": c["text"][:250],
            }
            for c in chunks[:3]
        ]

        return DocumentUploadResponse(
            document_id=document_id,
            filename=filename,
            total_pages=total_pages,
            characters_extracted=total_chars,
            text_preview=full_text[:1500],
            stored=True,
            indexed=indexed_successfully,
            already_exists=False,
            chunk_count=len(chunks),
            chunk_preview=chunk_previews,
            message=msg,
            session_id=session_id,
        )


    def reindex_owned_document(
        self,
        document_id: str,
        *,
        user_id: str
    ) -> Dict[str, Any]:

        if not user_id:
            raise ValueError("Authentication is required.")

        document = self.repo.get_user_document(
            document_id, user_id
        )

        if not document:
            raise ValueError("Document not found.")

        workspace_id = document["workspace_id"]
        filename = document["filename"]

        metadata = dict(document.get("metadata") or {})

        object_key = (
            metadata.get("object_key")
            or document.get("stored_filename")
        )

        file_bytes = self.storage.get_file_bytes(
            document_id,
            object_key=object_key
        )

        if not file_bytes:
            raise ValueError("Original PDF is unavailable.")

        if len(file_bytes) > self.settings.max_file_size:
            raise ValueError("PDF exceeds the file size limit.")

        file_hash = hashlib.sha256(file_bytes).hexdigest()

        if file_hash != document["sha256"]:
            raise ValueError("Stored PDF integrity check failed.")

        parsed_pages = self.parser.parse_pdf(file_bytes)

        total_pages = len(parsed_pages)

        full_text = "\n\n".join(
            p.text for p in parsed_pages if p.text
        ).strip()

        chunks = self.chunker.chunk_pages(
            parsed_pages,
            document_id,
            filename
        )

        if not chunks:
            raise ValueError("No indexable text found in PDF.")

        for chunk in chunks:
            chunk["user_id"] = user_id
            chunk["workspace_id"] = workspace_id

        embeddings = generate_embeddings(
            [chunk["text"] for chunk in chunks]
        )

        self.vector_store.upsert_chunks(
            chunks, embeddings
        )

        verified_chunks = self.vector_store.get_chunks_by_document(
            document_id,
            user_id=user_id,
            workspace_id=workspace_id
        )

        expected_ids = {
            chunk["chunk_id"] for chunk in chunks
        }

        actual_ids = {
            chunk["chunk_id"] for chunk in verified_chunks
        }

        if expected_ids != actual_ids:
            raise RuntimeError(
                "Vector index verification failed."
            )

        metadata.update({
            "tables_detected": sum(
                len(p.tables) for p in parsed_pages
            ),
            "embedding_dimension": get_embedding_dimension(),
            "ownership_verified": True
        })

        self.repo.update_document_indexed(
            document_id=document_id,
            indexed=1,
            chunk_count=len(chunks),
            total_pages=total_pages,
            total_characters=len(full_text),
            metadata=metadata
        )

        return {
            "document_id": document_id,
            "total_pages": total_pages,
            "total_characters": len(full_text),
            "chunk_count": len(chunks),
            "indexed": True
        }
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        filter_tables_only: Optional[bool] = None,
        *,
        user_id: str
    ) -> SearchResponse:

        clean_query = query.strip()

        if not clean_query:
            raise ValueError("Query must not be empty.")

        if not user_id:
            raise ValueError("Authentication is required.")

        session = None

        if session_id:
            session = self.repo.get_user_session(
                session_id, user_id
            )

            if not session:
                raise ValueError("Session not found.")

        if document_id:
            document_ids = [document_id]

        elif session:
            document_ids = session.get("document_ids") or []

        else:
            document_ids = [
                d["document_id"]
                for d in self.repo.list_user_documents(
                    user_id=user_id
                )
                if d.get("indexed")
            ]

        documents = []

        for doc_id in dict.fromkeys(document_ids):

            doc = self.repo.get_user_document(
                doc_id, user_id
            )

            if not doc:
                raise ValueError("Document not found.")

            if session:
                if (
                    doc["workspace_id"] != session["workspace_id"]
                    or doc_id not in (session.get("document_ids") or [])
                ):
                    raise ValueError("Document not found in session.")

            if doc.get("indexed"):
                documents.append(doc)

        raw_results = []

        if documents:

            query_emb = generate_embeddings([clean_query])[0]

            for doc in documents:

                filters = {
                    "document_id": doc["document_id"],
                    "user_id": user_id,
                    "workspace_id": doc["workspace_id"]
                }

                if filter_tables_only:
                    filters["is_table"] = True

                matches = self.vector_store.search_chunks(
                    query_embedding=query_emb,
                    top_k=top_k,
                    filters=filters
                )

                for match in matches:

                    metadata = match.get("metadata") or {}

                    if all(
                        metadata.get(key) == value
                        for key, value in filters.items()
                    ):
                        raw_results.append(match)

        raw_results.sort(
            key=lambda r: r["distance"]
        )

        items = [
            SearchResultItem(
                chunk_id=r["chunk_id"],
                text=r["text"],
                metadata=r["metadata"],
                distance=r["distance"],
                score=r.get("score")
            )
            for r in raw_results[:top_k]
        ]

        return SearchResponse(
            query=clean_query,
            result_count=len(items),
            results=items,
            retriever_used=type(self.vector_store).__name__
        )

    def get_document_summary(self, document_id: str) -> Optional[DocumentSummary]:
        """Fetch full document summary from repository."""
        doc = self.repo.get_document_by_id(document_id)
        if not doc:
            return None

        return DocumentSummary(
            document_id=doc["document_id"],
            workspace_id=doc.get("workspace_id"),
            filename=doc["filename"],
            stored_filename=doc["stored_filename"],
            sha256=doc["sha256"],
            total_pages=doc.get("total_pages", 0),
            total_characters=doc.get("total_characters", 0),
            chunk_count=doc.get("chunk_count", 0),
            indexed=bool(doc.get("indexed", 0)),
            created_at=doc["created_at"],
            metadata=doc.get("metadata", {}),
        )

    def ingest_seed_documents(self) -> List[SeedDocumentResult]:
        """Process and index preloaded seed financial documents."""
        seed_dir = Path(self.settings.seed_docs_dir)
        results: List[SeedDocumentResult] = []

        # Ensure seed PDFs exist
        pdf_files = list(seed_dir.glob("*.pdf")) if seed_dir.exists() else []
        if not pdf_files:
            try:
                from app.infrastructure.document_processing.seed_generator import generate_seed_pdf_files
                pdf_files = generate_seed_pdf_files(seed_dir)
            except Exception as e:
                logger.warning("Could not auto-generate seed PDFs: %s", e)

        for pdf_file in sorted(pdf_files):
            try:
                data = pdf_file.read_bytes()
                resp = self.process_pdf_upload(
                    file_bytes=data,
                    filename=pdf_file.name,
                    workspace_id="default-workspace",
                )
                results.append(
                    SeedDocumentResult(
                        filename=pdf_file.name,
                        document_id=resp.document_id,
                        status="Indexed" if resp.indexed else "Failed",
                        pages=resp.total_pages,
                        chunks=resp.chunk_count,
                    )
                )
            except Exception as e:
                logger.error("Error processing seed document %s: %s", pdf_file.name, e)
                results.append(
                    SeedDocumentResult(
                        filename=pdf_file.name,
                        document_id="",
                        status=f"Error: {e}",
                        pages=0,
                        chunks=0,
                    )
                )

        return results

