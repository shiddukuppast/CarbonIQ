import hashlib
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_db_service import VectorDbService

logger = logging.getLogger("carboniq.rag.documents")

# Standardized knowledge categories required by CarbonIQ
STANDARD_CATEGORIES = {
    "electricity": "Electricity and Energy Efficiency",
    "energy": "Electricity and Energy Efficiency",
    "electricity_and_energy_efficiency": "Electricity and Energy Efficiency",
    "transportation": "Transportation and Sustainable Mobility",
    "mobility": "Transportation and Sustainable Mobility",
    "transportation_and_sustainable_mobility": "Transportation and Sustainable Mobility",
    "waste": "Waste Management and Circular Economy",
    "circular": "Waste Management and Circular Economy",
    "waste_management_and_circular_economy": "Waste Management and Circular Economy",
}


def normalize_category(raw_category: str) -> str:
    """Normalizes arbitrary folder or category names into one of the 3 standard domains."""
    c = (raw_category or "").strip().lower().replace("-", "_").replace(" ", "_")
    for key, standard_name in STANDARD_CATEGORIES.items():
        if key in c:
            return standard_name
    return "Electricity and Energy Efficiency"  # Default baseline


class DocumentService:
    """
    Handles document ingestion pipeline:
    Document Loading -> Text Extraction -> Text Cleaning -> Document Chunking ->
    Metadata Assignment -> Embedding Generation -> Qdrant Storage.

    Supports:
    - PDF files via pypdf.
    - DOCX files via python-docx.
    - Plain-text / Markdown files (.txt, .md).
    - Incremental indexing via SHA-256 content hashing.
    - Safe handling of empty, corrupt, or unreadable files.
    """

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Removes null bytes, excessive whitespaces, and normalizes linebreaks."""
        if not text:
            return ""
        # Remove null characters and control codes
        cleaned = text.replace("\x00", " ")
        cleaned = re.sub(r"[\r\t\f\v]", " ", cleaned)
        # Normalize multiple spaces and multiple newlines
        cleaned = re.sub(r" +", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @classmethod
    def extract_text_from_file(cls, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts raw text and inherent document metadata from PDF, DOCX, or text files.
        Returns (extracted_text, metadata_dict).
        """
        suffix = file_path.suffix.lower()
        metadata: Dict[str, Any] = {
            "file_name": file_path.name,
            "file_extension": suffix,
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }

        if suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                pages_text = []
                for p in reader.pages:
                    pt = p.extract_text()
                    if pt:
                        pages_text.append(pt)
                metadata["page_count"] = len(reader.pages)
                if reader.metadata:
                    if reader.metadata.title:
                        metadata["title"] = reader.metadata.title
                    if reader.metadata.author:
                        metadata["author"] = reader.metadata.author
                    if reader.metadata.creation_date:
                        metadata["publication_date"] = str(reader.metadata.creation_date)
                return cls.clean_text("\n\n".join(pages_text)), metadata
            except Exception as e:
                logger.warning(f"Error parsing PDF file {file_path}: {e}")
                return "", metadata

        elif suffix in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(str(file_path))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                # Include table contents
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            paragraphs.append(row_text)
                core_props = doc.core_properties
                if core_props:
                    if core_props.title:
                        metadata["title"] = core_props.title
                    if core_props.author:
                        metadata["author"] = core_props.author
                    if core_props.created:
                        metadata["publication_date"] = str(core_props.created)
                return cls.clean_text("\n\n".join(paragraphs)), metadata
            except Exception as e:
                logger.warning(f"Error parsing DOCX file {file_path}: {e}")
                return "", metadata

        else:
            # Plain-text or Markdown (.txt, .md, .rst)
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                # Parse YAML-like or header metadata if present
                lines = content.splitlines()
                title = None
                source = None
                for line in lines[:10]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                    elif line.lower().startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"\'')
                    elif line.lower().startswith("source:"):
                        source = line.split(":", 1)[1].strip().strip('"\'')
                if title:
                    metadata["title"] = title
                if source:
                    metadata["source"] = source
                return cls.clean_text(content), metadata
            except Exception as e:
                logger.warning(f"Error reading plain-text file {file_path}: {e}")
                return "", metadata

    @classmethod
    def chunk_text(
        cls,
        text: str,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> List[str]:
        """
        Chunks text into semantically coherent segments using paragraph and sentence boundaries.
        Avoids splitting words in half.
        """
        if not text or not text.strip():
            return []

        # Split initially by paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            if len(para) > chunk_size:
                # If paragraph itself is too large, split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        current_chunk = (current_chunk + " " + sent).strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            # Keep overlap from tail of previous chunk
                            overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                            current_chunk = (overlap_text + " " + sent).strip()
                        else:
                            # Long single sentence, chunk with slice
                            chunks.append(sent[:chunk_size])
                            current_chunk = sent[chunk_size - chunk_overlap:]
            else:
                if len(current_chunk) + len(para) + 1 <= chunk_size:
                    current_chunk = (current_chunk + "\n\n" + para).strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                        current_chunk = (overlap_text + "\n\n" + para).strip()
                    else:
                        current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Filter out trivial chunks
        return [c for c in chunks if len(c.strip()) > 25]

    @classmethod
    def index_single_document(
        cls,
        file_path: Path,
        category: Optional[str] = None,
        source: Optional[str] = None,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Indexes a single file into Qdrant.
        - Calculates document SHA-256.
        - If already indexed and unchanged, skips embedding generation unless force_reindex=True.
        - Returns indexing summary.
        """
        if not file_path.exists() or file_path.is_dir():
            return {"status": "error", "error": f"File {file_path} does not exist."}

        text, doc_meta = cls.extract_text_from_file(file_path)
        if not text or len(text.strip()) < 30:
            return {"status": "skipped", "reason": "Document is empty or contains insufficient text.", "file": file_path.name}

        # Deterministic document ID based on normalized file path
        norm_path = str(file_path.resolve()).lower()
        doc_id = hashlib.sha256(norm_path.encode("utf-8")).hexdigest()[:16]
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Inferred or explicit category
        inferred_category = category or doc_meta.get("category") or file_path.parent.name
        norm_category = normalize_category(inferred_category)

        # Document title
        doc_title = doc_meta.get("title") or file_path.stem.replace("_", " ").replace("-", " ").title()
        doc_source = source or doc_meta.get("source") or f"CarbonIQ Knowledge Base ({file_path.name})"
        pub_date = doc_meta.get("publication_date")

        # Chunk the cleaned text
        raw_chunks = cls.chunk_text(text, chunk_size=650, chunk_overlap=120)
        if not raw_chunks:
            return {"status": "skipped", "reason": "No valid text chunks produced.", "file": file_path.name}

        # Clean prior index points for this document ID to ensure updates don't leave stale chunks
        VectorDbService.delete_document(doc_id)

        # Generate embeddings in batch locally via Sentence Transformers
        embeddings = EmbeddingService.embed_batch(raw_chunks)

        # Build Qdrant points
        points_to_upsert = []
        for idx, (chunk_text_content, emb) in enumerate(zip(raw_chunks, embeddings)):
            chunk_id = hashlib.sha256(f"{doc_id}_{idx}_{content_hash}".encode("utf-8")).hexdigest()[:24]
            payload = {
                "text": chunk_text_content,
                "title": doc_title,
                "source": doc_source,
                "category": norm_category,
                "doc_id": doc_id,
                "chunk_index": idx,
                "total_chunks": len(raw_chunks),
                "file_name": file_path.name,
                "content_hash": content_hash,
                "publication_date": pub_date,
            }
            points_to_upsert.append({
                "id": chunk_id,
                "vector": emb,
                "payload": payload,
            })

        count = VectorDbService.upsert_chunks(points_to_upsert)
        return {
            "status": "success",
            "doc_id": doc_id,
            "title": doc_title,
            "category": norm_category,
            "chunks_indexed": count,
            "file": file_path.name,
        }

    @classmethod
    def index_knowledge_directory(
        cls,
        knowledge_dir: Optional[Path] = None,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Crawls knowledge directory, categorizing documents by subfolder:
        1. Electricity and Energy Efficiency
        2. Transportation and Sustainable Mobility
        3. Waste Management and Circular Economy
        """
        if knowledge_dir is None:
            backend_dir = Path(__file__).resolve().parents[2]
            knowledge_dir = backend_dir / settings.KNOWLEDGE_BASE_DIR

        if not knowledge_dir.exists():
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            return {
                "status": "empty",
                "message": f"Knowledge directory '{knowledge_dir}' was created. Please add source documents.",
                "total_indexed": 0,
                "files_processed": 0,
            }

        supported_exts = {".pdf", ".docx", ".txt", ".md"}
        processed_files = []
        total_chunks = 0
        errors = []

        for root, _, files in os.walk(knowledge_dir):
            rel_folder = Path(root).relative_to(knowledge_dir).as_posix()
            folder_category = normalize_category(rel_folder)

            for f in files:
                f_path = Path(root) / f
                if f_path.suffix.lower() in supported_exts:
                    try:
                        res = cls.index_single_document(
                            file_path=f_path,
                            category=folder_category,
                            force_reindex=force_reindex,
                        )
                        if res.get("status") == "success":
                            total_chunks += res.get("chunks_indexed", 0)
                            processed_files.append(res)
                        elif res.get("status") == "error":
                            errors.append(res)
                    except Exception as err:
                        logger.error(f"Failed to index file {f_path}: {err}")
                        errors.append({"file": f, "error": str(err)})

        return {
            "status": "completed",
            "knowledge_dir": str(knowledge_dir),
            "files_processed": len(processed_files),
            "total_chunks_indexed": total_chunks,
            "details": processed_files,
            "errors": errors,
        }

