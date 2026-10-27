"""
Bank SOP Knowledge Base & RAG Retrieval module.
Ingests PDF, Markdown, and TXT policy documents, extracts chunks,
preserves policy identifiers, and performs dense embedding retrieval via Ollama.
Includes local caching to prevent redundant Ollama model swapping.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import requests

from src.schemas import SOPPassage, CustomerContext

SOP_DIR = Path(__file__).resolve().parent.parent / "data" / "sops"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / ".cache"
POLICY_ID_REGEX = re.compile(r'(?:SOP Identifier|Policy Identifier|SOP ID)[:\s]*([A-Z0-9\-]+)', re.IGNORECASE)
POLICY_TITLE_REGEX = re.compile(r'(?:Policy Title|Title)[:\s]*([^\n\r]+)', re.IGNORECASE)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract clean text from a PDF document using pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    pages_text = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            pages_text.append(txt)
    return "\n\n".join(pages_text)


class SOPKnowledgeBase:
    def __init__(
        self,
        sops_dir: Path = SOP_DIR,
        cache_dir: Path = CACHE_DIR,
        ollama_url: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text:latest"
    ):
        self.sops_dir = sops_dir
        self.cache_dir = cache_dir
        self.ollama_url = ollama_url
        self.embed_model = embed_model
        self.passages: List[SOPPassage] = []
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_mode = "Ollama (nomic-embed-text)"
        self.build_index()

    def _extract_metadata(self, filename: str, content: str) -> Dict[str, str]:
        """Extract SOP ID and Title from document header or filename."""
        policy_id = "SOP-GENERAL"
        id_match = POLICY_ID_REGEX.search(content[:1000])
        if id_match:
            policy_id = id_match.group(1).strip()
        elif "IMPS" in filename.upper():
            policy_id = "SOP-IMPS-001"
        elif "UPI" in filename.upper():
            policy_id = "SOP-UPI-002"
        elif "CARD" in filename.upper():
            policy_id = "SOP-CARD-003"
        elif "ATM" in filename.upper():
            policy_id = "SOP-ATM-004"

        title = filename.replace("_", " ").replace(".md", "").replace(".txt", "").replace(".pdf", "")
        title_match = POLICY_TITLE_REGEX.search(content[:1000])
        if title_match:
            title = title_match.group(1).strip()

        return {"policy_id": policy_id, "policy_title": title}

    def _split_into_chunks(self, content: str, meta: Dict[str, str], doc_name: str) -> List[SOPPassage]:
        """Split document text into cohesive policy paragraphs/sections."""
        raw_sections = re.split(r'\n(?=#{1,3}\s+|\d+\.\s+)', content)
        chunks = []

        for sec in raw_sections:
            clean_sec = sec.strip()
            if len(clean_sec) < 60:
                continue

            first_line = clean_sec.splitlines()[0][:80].replace("#", "").strip()

            chunks.append(
                SOPPassage(
                    doc_name=doc_name,
                    policy_id=meta["policy_id"],
                    policy_title=meta["policy_title"],
                    section=first_line,
                    content=clean_sec,
                    similarity_score=0.0
                )
            )

        return chunks

    def _get_files_fingerprint(self, files: List[Path]) -> str:
        """Create a hash of file modification timestamps and sizes."""
        h = hashlib.md5()
        for f in sorted(files):
            stat = f.stat()
            h.update(f"{f.name}:{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
        return h.hexdigest()

    def build_index(self, force_rebuild: bool = False) -> int:
        """
        Scan data/sops/, parse all documents, and compute or load cached embeddings.
        Returns total number of indexed passages.
        """
        if not self.sops_dir.exists():
            self.sops_dir.mkdir(parents=True, exist_ok=True)
            return 0

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_vec_file = self.cache_dir / "embeddings.npz"
        cache_meta_file = self.cache_dir / "passages.json"

        supported_extensions = [".md", ".txt", ".pdf"]
        files = [p for p in self.sops_dir.iterdir() if p.suffix.lower() in supported_extensions]

        current_fingerprint = self._get_files_fingerprint(files)

        # Check if cache is valid
        if not force_rebuild and cache_vec_file.exists() and cache_meta_file.exists():
            try:
                with open(cache_meta_file, "r", encoding="utf-8") as f:
                    cache_info = json.load(f)
                if cache_info.get("fingerprint") == current_fingerprint:
                    self.passages = [SOPPassage(**p) for p in cache_info.get("passages", [])]
                    loaded_npz = np.load(str(cache_vec_file))
                    self.embeddings = loaded_npz["embeddings"]
                    self.embedding_mode = f"Cached Dense Vectors ({self.embed_model})"
                    return len(self.passages)
            except Exception:
                pass  # On cache read failure, fall through to re-indexing

        # Re-index documents
        self.passages = []
        for doc_path in files:
            try:
                if doc_path.suffix.lower() == ".pdf":
                    content = extract_text_from_pdf(doc_path)
                else:
                    with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                meta = self._extract_metadata(doc_path.name, content)
                doc_chunks = self._split_into_chunks(content, meta, doc_path.name)
                self.passages.extend(doc_chunks)
            except Exception as e:
                print(f"Error processing {doc_path.name}: {e}")

        # Compute embeddings
        if self.passages:
            self._compute_embeddings()

            # Save to cache
            if self.embeddings is not None and "Ollama" in self.embedding_mode:
                try:
                    np.savez_compressed(str(cache_vec_file), embeddings=self.embeddings)
                    cache_data = {
                        "fingerprint": current_fingerprint,
                        "passages": [p.model_dump() for p in self.passages]
                    }
                    with open(cache_meta_file, "w", encoding="utf-8") as f:
                        json.dump(cache_data, f, indent=2)
                except Exception as e:
                    print(f"Failed to write cache: {e}")

        return len(self.passages)

    def _compute_embeddings(self) -> None:
        """Compute dense vectors via Ollama or fallback to lexical vectors."""
        vectors = []
        use_ollama = True

        for p in self.passages:
            text_to_embed = f"{p.policy_title} - {p.section}: {p.content}"
            vec = self._get_ollama_embedding(text_to_embed)
            if vec is None:
                use_ollama = False
                break
            vectors.append(vec)

        if use_ollama and vectors:
            self.embeddings = np.array(vectors, dtype=np.float32)
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.embeddings = self.embeddings / norms
            self.embedding_mode = f"Ollama Dense Vectors ({self.embed_model})"
        else:
            self._compute_fallback_lexical_index()

    def _get_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """Fetch embedding vector from Ollama HTTP server."""
        try:
            resp = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding")
        except Exception:
            pass
        return None

    def _compute_fallback_lexical_index(self) -> None:
        """Lightweight bag-of-words / TF representation as offline fallback."""
        self.embedding_mode = "Lexical Fallback (Term Frequency)"
        vocab = {}
        for p in self.passages:
            words = re.findall(r'\b\w{3,}\b', p.content.lower())
            for w in words:
                if w not in vocab:
                    vocab[w] = len(vocab)

        self.vocab = vocab
        vectors = []
        for p in self.passages:
            vec = np.zeros(len(vocab), dtype=np.float32)
            words = re.findall(r'\b\w{3,}\b', p.content.lower())
            for w in words:
                if w in vocab:
                    vec[vocab[w]] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        self.embeddings = np.array(vectors, dtype=np.float32)

    def retrieve(self, query: str, top_k: int = 3, customer: Optional[CustomerContext] = None) -> List[SOPPassage]:
        """
        Retrieve top_k most relevant SOP passages for customer query.
        Returns ranked list of SOPPassage objects with similarity_score.
        """
        if not self.passages or self.embeddings is None:
            return []

        # Vectorize query
        if "Dense" in self.embedding_mode or "Ollama" in self.embedding_mode:
            q_vec = self._get_ollama_embedding(query)
            if q_vec is not None:
                q_arr = np.array(q_vec, dtype=np.float32)
                q_norm = np.linalg.norm(q_arr)
                if q_norm > 0:
                    q_arr = q_arr / q_norm
                scores = np.dot(self.embeddings, q_arr).copy()
            else:
                scores = self._score_lexical(query).copy()
        else:
            scores = self._score_lexical(query).copy()

        # Contextual affinity boost if customer's active transaction channel aligns
        if customer:
            channel_kw = ""
            tt = (customer.transaction_type or "").upper()
            ti = (customer.transaction_id or "").upper()
            if "UPI" in tt or "UPI" in ti:
                channel_kw = "UPI"
            elif "IMPS" in tt or "IMPS" in ti:
                channel_kw = "IMPS"
            elif "CARD" in tt or "POS" in tt or "CARD" in ti:
                channel_kw = "CARD"
            elif "ATM" in tt or "ATM" in ti:
                channel_kw = "ATM"

            if channel_kw:
                for idx, p in enumerate(self.passages):
                    if channel_kw in p.policy_id.upper() or channel_kw in p.policy_title.upper():
                        scores[idx] += 0.06

        # Rank indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if "Dense" in self.embedding_mode or "Ollama" in self.embedding_mode:
                # Calibrate typical dense cosine range [0.48, 0.65] to [0.0, 1.0]
                norm_score = max(0.0, min(1.0, (score - 0.48) / 0.17))
            else:
                norm_score = max(0.0, min(1.0, score))

            passage = self.passages[idx]
            results.append(
                SOPPassage(
                    doc_name=passage.doc_name,
                    policy_id=passage.policy_id,
                    policy_title=passage.policy_title,
                    section=passage.section,
                    content=passage.content,
                    similarity_score=round(norm_score, 3)
                )
            )

        return results

    def _score_lexical(self, query: str) -> np.ndarray:
        """Compute cosine similarity using lexical vocabulary."""
        if not hasattr(self, 'vocab') or not self.vocab:
            return np.zeros(len(self.passages), dtype=np.float32)
        q_vec = np.zeros(len(self.vocab), dtype=np.float32)
        words = re.findall(r'\b\w{3,}\b', query.lower())
        for w in words:
            if w in self.vocab:
                q_vec[self.vocab[w]] += 1.0
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm
        return np.dot(self.embeddings, q_vec)
