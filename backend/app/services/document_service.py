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

                # Heuristic auto-detection from front pages if PDF metadata is omitted
                if pages_text:
                    front_sample = "\n".join(pages_text[:3])
                    if not metadata.get("title") and "CO2 Baseline Database" in front_sample:
                        metadata["title"] = "CO2 Baseline Database for the Indian Power Sector"
                    if not metadata.get("source") and "Central Electricity Authority" in front_sample:
                        metadata["source"] = "Central Electricity Authority"
                    v_match = re.search(r"Version\s+([\d\.]+)", front_sample, re.IGNORECASE)
                    if v_match and not metadata.get("document_version"):
                        metadata["document_version"] = v_match.group(1)
                    d_match = re.search(
                        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
                        front_sample,
                        re.IGNORECASE,
                    )
                    if d_match and not metadata.get("publication_date"):
                        metadata["publication_date"] = d_match.group(0)
                    rp_match = re.search(r"\bFY\s+\d{4}[-–]\d{2,4}\b", front_sample, re.IGNORECASE)
                    if rp_match and not metadata.get("reporting_period"):
                        metadata["reporting_period"] = rp_match.group(0)
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
        if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_size must be positive and chunk_overlap must be smaller than chunk_size.")

        text = cls.clean_text(text)
        chunks: List[str] = []
        start = 0
        while start < len(text):
            hard_end = min(start + chunk_size, len(text))
            end = hard_end
            if hard_end < len(text):
                search_start = start + (chunk_size * 3 // 5)
                segment = text[search_start:hard_end]
                sentence_breaks = list(re.finditer(r"(?<=[.!?])\s+|\n\n", segment))
                breaks = sentence_breaks or list(re.finditer(r"\s+", segment))
                if breaks:
                    end = search_start + breaks[-1].start()

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break

            next_start = max(start + 1, end - chunk_overlap)
            while next_start < end and not text[next_start].isspace():
                next_start += 1
            while next_start < end and text[next_start].isspace():
                next_start += 1
            start = next_start if next_start > start else end

        # Filter out trivial chunks
        return [c for c in chunks if len(c.strip()) > 25]

    @classmethod
    def index_single_document(
        cls,
        file_path: Path,
        category: Optional[str] = None,
        source: Optional[str] = None,
        title: Optional[str] = None,
        document_version: Optional[str] = None,
        reporting_period: Optional[str] = None,
        publication_date: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
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

        if not VectorDbService.is_available():
            return {
                "status": "error",
                "error": VectorDbService.get_last_error() or "Qdrant is unavailable.",
                "file": file_path.name,
            }
        if not force_reindex and VectorDbService.get_document_content_hash(doc_id) == content_hash:
            return {
                "status": "unchanged",
                "doc_id": doc_id,
                "file": file_path.name,
                "chunks_indexed": 0,
            }

        # Inferred or explicit category
        inferred_category = category or doc_meta.get("category") or file_path.parent.name
        norm_category = normalize_category(inferred_category)

        # Document title & attributes
        doc_title = title or doc_meta.get("title") or file_path.stem.replace("_", " ").replace("-", " ").title()
        doc_source = source or doc_meta.get("source") or f"CarbonIQ Knowledge Base ({file_path.name})"
        pub_date = publication_date or doc_meta.get("publication_date")
        doc_version = document_version or doc_meta.get("document_version")
        rep_period = reporting_period or doc_meta.get("reporting_period")

        # Chunk the cleaned text
        raw_chunks = cls.chunk_text(text, chunk_size=650, chunk_overlap=120)
        if not raw_chunks:
            return {"status": "skipped", "reason": "No valid text chunks produced.", "file": file_path.name}

        # Generate embeddings in batch locally via Sentence Transformers
        embeddings = EmbeddingService.embed_batch(raw_chunks)
        if len(embeddings) != len(raw_chunks):
            raise ValueError("Embedding batch size does not match the document chunk count.")

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
                "document_version": doc_version,
                "reporting_period": rep_period,
            }
            if extra_metadata:
                payload.update(extra_metadata)
            points_to_upsert.append({
                "id": chunk_id,
                "vector": emb,
                "payload": payload,
            })

        # Replace old points only after text extraction and embedding succeed.
        if not VectorDbService.delete_document(doc_id):
            return {
                "status": "error",
                "error": VectorDbService.get_last_error() or "Existing document chunks could not be removed.",
                "doc_id": doc_id,
                "file": file_path.name,
            }
        count = VectorDbService.upsert_chunks(points_to_upsert)
        if count != len(points_to_upsert):
            return {
                "status": "error",
                "error": f"Qdrant stored {count} of {len(points_to_upsert)} document chunks.",
                "doc_id": doc_id,
                "file": file_path.name,
            }
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
                        elif res.get("status") == "unchanged":
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
