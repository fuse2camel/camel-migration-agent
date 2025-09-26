"""
Camel Migration Knowledge Base with FAISS and HuggingFace embeddings
Provides vector search and fallback patterns for Red Hat Camel 4.10 migration
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


class CamelKnowledgeBase:
    """
    Knowledge base for Red Hat Camel migration using FAISS and HuggingFace embeddings.
    Provides both vector search (when PDFs are ingested) and fallback patterns.
    """

    def __init__(
        self,
        persist_dir: str = "knowledge/vector_db",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the knowledge base.

        Args:
            persist_dir: Directory to persist the vector database
            model_name: HuggingFace model name for embeddings
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name

        # Initialize SentenceTransformer
        try:
            cache_dir = str(self.persist_dir / "model_cache")
            self.encoder = SentenceTransformer(model_name, device="cpu", cache_folder=cache_dir)
            self.embed_dim = self.encoder.get_sentence_embedding_dimension()
            logger.info(f"Initialized {model_name} with dimension {self.embed_dim}")
            self.ready = True
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings: {e}. Using fallback mode.")
            self.ready = False
            self.embed_dim = 384

        # Storage
        self.index = None
        self.documents = []
        self.metadata = []

        # Load existing index if available
        self._load_index()

    def _load_index(self) -> bool:
        """Load existing FAISS index from disk."""
        index_path = self.persist_dir / "faiss.index"
        docs_path = self.persist_dir / "documents.pkl"
        meta_path = self.persist_dir / "metadata.pkl"

        if all(p.exists() for p in [index_path, docs_path, meta_path]):
            try:
                self.index = faiss.read_index(str(index_path))
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                with open(meta_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
                return True
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
        return False

    def _extract_text_from_pdf(self, pdf_path: str, chunk_size: int = 500) -> List[str]:
        """
        Extract text from PDF file and split into chunks.

        Args:
            pdf_path: Path to PDF file
            chunk_size: Approximate size of each text chunk

        Returns:
            List of text chunks
        """
        chunks = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # Split into overlapping chunks
                    for i in range(0, len(text), chunk_size - 100):
                        chunk = text[i:i + chunk_size].strip()
                        if chunk and len(chunk) > 50:  # Skip very small chunks
                            chunks.append(chunk)
        except Exception as e:
            logger.error(f"Failed to extract from {pdf_path}: {e}")
        return chunks

    def ingest_documents(
        self,
        docs_path: str = "knowledge/docs",
        force_reingest: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest PDF documents into the vector database.

        Args:
            docs_path: Path to documents directory
            force_reingest: Force re-ingestion even if index exists

        Returns:
            Dictionary with ingestion results
        """
        if not self.ready:
            return {
                "status": "error",
                "message": "Embeddings not ready. Knowledge base will work in fallback mode."
            }

        # Check if we should skip ingestion
        if self.index is not None and not force_reingest:
            return {
                "status": "skipped",
                "message": "Index already exists. Use force_reingest=True to rebuild."
            }

        docs_path = Path(docs_path)
        if not docs_path.exists():
            return {
                "status": "error",
                "message": f"Documents path {docs_path} does not exist"
            }

        # Extract text from all PDFs
        all_chunks = []
        all_metadata = []

        pdf_files = list(docs_path.glob("*.pdf"))
        if not pdf_files:
            return {
                "status": "error",
                "message": "No PDF files found in directory"
            }

        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file.name}")
            chunks = self._extract_text_from_pdf(str(pdf_file))
            all_chunks.extend(chunks)
            all_metadata.extend([
                {"file": pdf_file.name, "chunk_idx": i}
                for i in range(len(chunks))
            ])

        if not all_chunks:
            return {
                "status": "error",
                "message": "No text extracted from PDFs"
            }

        # Create embeddings
        logger.info(f"Creating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.encoder.encode(
            all_chunks,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.embed_dim)
        self.index.add(embeddings.astype(np.float32))
        self.documents = all_chunks
        self.metadata = all_metadata

        # Persist
        self._save_index()

        return {
            "status": "success",
            "chunks_indexed": len(all_chunks),
            "files_processed": len(pdf_files)
        }

    def _save_index(self):
        """Save index and metadata to disk."""
        try:
            faiss.write_index(self.index, str(self.persist_dir / "faiss.index"))
            with open(self.persist_dir / "documents.pkl", 'wb') as f:
                pickle.dump(self.documents, f)
            with open(self.persist_dir / "metadata.pkl", 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info("Index saved successfully")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Query the knowledge base for relevant information.

        Args:
            query_text: The query to search for
            top_k: Number of top results to return
            include_sources: Whether to include source references

        Returns:
            Dictionary with query results
        """
        # Use vector search if available, otherwise fallback
        if not self.ready or self.index is None or self.index.ntotal == 0:
            return {
                "status": "fallback",
                "query": query_text,
                "response": self._get_fallback_response(query_text),
                "message": "Using built-in migration patterns (vector search not available)"
            }

        try:
            # Encode query
            query_embedding = self.encoder.encode([query_text], convert_to_numpy=True)

            # Search FAISS index
            distances, indices = self.index.search(query_embedding.astype(np.float32), top_k)

            # Get results
            results = []
            response_texts = []

            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    doc_text = self.documents[idx]
                    response_texts.append(doc_text)

                    if include_sources:
                        results.append({
                            "text": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                            "score": float(dist),
                            "file": self.metadata[idx]["file"] if idx < len(self.metadata) else "unknown"
                        })

            # Combine top results for response
            response = "\n\n---\n\n".join(response_texts[:3]) if response_texts else self._get_fallback_response(query_text)

            result = {
                "status": "success",
                "query": query_text,
                "response": response,
                "num_results": len(response_texts)
            }

            if include_sources:
                result["sources"] = results

            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "status": "fallback",
                "query": query_text,
                "response": self._get_fallback_response(query_text),
                "message": f"Query error: {str(e)}. Using fallback patterns."
            }

    def get_dsl_conversion_help(
        self,
        xml_snippet: str = "",
        pattern_type: str = ""
    ) -> Dict[str, Any]:
        """
        Get DSL conversion guidance for XML to Java migration.

        Args:
            xml_snippet: Optional XML snippet to analyze
            pattern_type: Type of pattern (route, processor, etc.)

        Returns:
            Conversion guidance
        """
        query = f"Red Hat Camel 4.10 DSL conversion from XML to Java"
        if pattern_type:
            query += f" for {pattern_type}"
        if xml_snippet:
            query += f". Pattern: {xml_snippet[:100]}"

        result = self.query(query, top_k=3)

        # Add conversion patterns
        result["conversion_patterns"] = self._get_conversion_patterns()

        return result

    def get_component_migration_info(self, component_name: str) -> Dict[str, Any]:
        """
        Get component-specific migration information.

        Args:
            component_name: Name of the Camel component

        Returns:
            Component migration details
        """
        query = f"Red Hat Camel 4.10 migration for {component_name} component"
        result = self.query(query, top_k=3)

        # Add known component mappings
        mappings = self._get_component_mappings()
        if component_name in mappings:
            result["known_mapping"] = mappings[component_name]

        return result

    def _get_fallback_response(self, query_text: str) -> str:
        """
        Provide fallback response based on common migration patterns.

        Args:
            query_text: The query text

        Returns:
            Fallback response string
        """
        query_lower = query_text.lower()

        if "xml" in query_lower and ("java" in query_lower or "dsl" in query_lower):
            return """Red Hat Camel 4.10 XML to Java DSL Conversion:

1. Route Definition:
   XML: <route id="myRoute">
   Java: from("direct:start").routeId("myRoute")

2. Spring Integration:
   - Add @Component annotation to RouteBuilder classes
   - Use @Autowired for dependency injection

3. API Changes:
   - Use exchange.getMessage() instead of getIn()/getOut()
   - Import from org.apache.camel.support.* instead of org.apache.camel.impl.*

4. Common Patterns:
   - choice() → when() → otherwise() → end()
   - split().body() → streaming() → to()
   - process(exchange -> { ... }) for processors"""

        elif "spring boot" in query_lower:
            return """Red Hat Camel 4.10 with Spring Boot 3 Migration:

1. Dependencies:
   - Parent: com.redhat.camel.springboot:camel-spring-boot-bom:4.10.0.redhat-00001
   - Add Red Hat Maven repository: https://maven.repository.redhat.com/ga/

2. Configuration:
   - Update application.properties for Spring Boot 3
   - camel.springboot.* properties have changed

3. Requirements:
   - JDK 21 (use Eclipse Temurin)
   - Spring Boot 3.2.x
   - Jakarta EE instead of javax

4. Starters:
   - Use camel-spring-boot-starter
   - Component-specific starters (camel-http-starter, etc.)"""

        elif "component" in query_lower or "dependency" in query_lower:
            return """Red Hat Camel 4.10 Component Changes:

Dependency Mappings:
- camel-http4 → camel-http
- camel-jetty9 → camel-jetty
- camel-rabbitmq → camel-spring-rabbitmq
- camel-activemq → camel-jms (with ActiveMQ connection factory)

Configuration:
- Add Red Hat repository to pom.xml
- Use Red Hat build versions (*.redhat-00001)
- Update component URIs in routes"""

        elif "error" in query_lower or "exception" in query_lower:
            return """Common Red Hat Camel 4.10 Migration Errors:

1. Cannot find symbol (imports):
   - Update to org.apache.camel.support.*
   - Remove org.apache.camel.impl.*

2. Exchange API errors:
   - Replace getIn() with getMessage()
   - Replace getOut() with getMessage()

3. Missing dependencies:
   - Update to Red Hat BOM
   - Check component name changes

4. RouteBuilder issues:
   - Add @Component annotation
   - Ensure proper Spring configuration"""

        else:
            return """Red Hat Camel 4.10 Migration Guidelines:

1. Update Maven dependencies to Red Hat build versions
2. Migrate XML DSL to Java DSL with Spring Boot 3
3. Update Exchange API calls (getMessage())
4. Add proper Spring annotations (@Component)
5. Ensure JDK 21 compatibility
6. Update component names and configurations
7. Test with Red Hat certified components"""

    def _get_conversion_patterns(self) -> Dict[str, str]:
        """Get common XML to Java DSL conversion patterns."""
        return {
            "route": "from(uri).routeId(id).to(uri)",
            "choice": "choice().when(predicate).to(uri).otherwise().to(uri).end()",
            "split": "split(expression).streaming().to(uri)",
            "aggregate": "aggregate(expression).completionSize(n).to(uri)",
            "filter": "filter(predicate).to(uri)",
            "transform": "transform(expression)",
            "process": "process(exchange -> { /* logic */ })",
            "bean": "bean(MyBean.class, \"method\")",
            "multicast": "multicast().parallelProcessing().to(uri1, uri2)",
            "errorHandler": "errorHandler(deadLetterChannel(uri))"
        }

    def _get_component_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get component dependency mappings for Camel 4."""
        return {
            "http": {
                "old": "camel-http4",
                "new": "camel-http",
                "notes": "HTTP4 component merged into HTTP"
            },
            "jetty": {
                "old": "camel-jetty9",
                "new": "camel-jetty",
                "notes": "Jetty9 renamed to Jetty"
            },
            "rabbitmq": {
                "old": "camel-rabbitmq",
                "new": "camel-spring-rabbitmq",
                "notes": "Use Spring Boot starter"
            },
            "activemq": {
                "old": "camel-activemq",
                "new": "camel-jms",
                "notes": "Use JMS with ActiveMQ factory"
            },
            "mongodb": {
                "old": "camel-mongodb3",
                "new": "camel-mongodb",
                "notes": "MongoDB3 merged into MongoDB"
            }
        }


# Singleton instance
_kb_instance = None


def get_knowledge_base() -> CamelKnowledgeBase:
    """Get or create the knowledge base singleton instance."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = CamelKnowledgeBase()
    return _kb_instance


def initialize_knowledge_base(
    docs_path: str = "knowledge/docs",
    force_reingest: bool = False
) -> Dict[str, Any]:
    """
    Initialize and ingest documents into the knowledge base.

    Args:
        docs_path: Path to documents directory
        force_reingest: Force re-ingestion even if index exists

    Returns:
        Ingestion results
    """
    kb = get_knowledge_base()
    return kb.ingest_documents(docs_path, force_reingest)