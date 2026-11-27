from app.config import get_settings
from app.infrastructure.vector_store import get_vector_store

settings = get_settings()

print("Configured vector store:", settings.vector_store_type)
print("Chroma directory:", settings.chroma_db_dir)

store = get_vector_store()

print("Active vector store:", type(store).__name__)

print(
    "Internal backend:",
    getattr(store, "backend", "Not specified")
)

print("Healthy:", store.is_healthy())
print("Total indexed chunks:", store.count_chunks())