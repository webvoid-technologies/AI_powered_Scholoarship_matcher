"""ChromaDB vector store service for opportunities."""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from config import Config
from services.embedding_service import EmbeddingService, embedding_service


class ChromaServiceError(Exception):
    pass


COLLECTION_NAMES = ['scholarships', 'internships', 'hackathons', 'fellowships', 'certifications']


class ChromaService:
    """Manage ChromaDB collections for opportunity categories."""

    def __init__(self, config: Config = None, embedding_service: EmbeddingService = None):
        self.config = config or Config()
        self.persist_dir = self.config.CHROMA_PERSIST_DIR
        self.collection_metadata = {'hnsw:space': 'cosine'}
        self._client = None
        self._collections: Dict[str, Any] = {}
        self.embedding_service = embedding_service or EmbeddingService()

    def _get_client(self):
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            try:
                self._client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception as exc:
                raise ChromaServiceError(f'Failed to initialize ChromaDB client: {exc}') from exc
        return self._client

    def get_collection(self, name: str, create: bool = True):
        """Get or create a ChromaDB collection."""
        name = name.lower().strip()
        if name not in COLLECTION_NAMES:
            raise ChromaServiceError(f'Unsupported collection name: {name}. Supported: {COLLECTION_NAMES}')

        if name not in self._collections:
            client = self._get_client()
            try:
                if create:
                    self._collections[name] = client.get_or_create_collection(
                        name=name,
                        metadata=self.collection_metadata
                    )
                else:
                    self._collections[name] = client.get_collection(name=name)
            except Exception as exc:
                raise ChromaServiceError(f'Failed to access collection "{name}": {exc}') from exc

        return self._collections[name]

    def upsert(self, category: str, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert or update opportunities in a collection."""
        if not opportunities:
            return {'success': True, 'inserted': 0, 'category': category}

        collection = self.get_collection(category)
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for opp in opportunities:
            doc = opp.get('document') or opp.get('description', '')
            if not doc:
                continue
            ids.append(opp['id'])
            documents.append(doc)
            metadatas.append(self._build_metadata(opp))
            embeddings.append(self.embedding_service.encode_single(doc))

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        except Exception as exc:
            raise ChromaServiceError(f'Failed to upsert documents: {exc}') from exc

        return {'success': True, 'inserted': len(ids), 'category': category}

    def delete(self, category: str, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delete documents by ID or metadata filter."""
        collection = self.get_collection(category)
        try:
            if ids:
                collection.delete(ids=ids)
            elif where:
                collection.delete(where=where)
            else:
                raise ChromaServiceError('Provide either ids or where filter for deletion.')
        except Exception as exc:
            raise ChromaServiceError(f'Failed to delete documents: {exc}') from exc
        return {'success': True, 'deleted': len(ids) if ids else 'filter-based', 'category': category}

    def search(
        self,
        category: str,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Semantic search within a collection."""
        collection = self.get_collection(category, create=False)
        query_embedding = self.embedding_service.encode_single(query)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=['documents', 'distances', 'metadatas'] if include_metadata else ['documents', 'distances']
            )
        except Exception as exc:
            raise ChromaServiceError(f'Query failed for collection "{category}": {exc}') from exc

        matches = []
        ids = results.get('ids', [[]])[0]
        documents = results.get('documents', [[]])[0]
        distances = results.get('distances', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0] if include_metadata else [None] * len(ids)

        for idx, doc_id in enumerate(ids):
            distance = distances[idx] if idx < len(distances) else 0.0
            score = max(0.0, round((1.0 - float(distance)) * 100, 2))
            match = {
                'id': doc_id,
                'document': documents[idx] if idx < len(documents) else '',
                'distance': float(distance),
                'score': score
            }
            if include_metadata and metadatas[idx]:
                meta = metadatas[idx]
                for key in ('title', 'organization', 'category', 'country', 'degree', 'deadline', 'url', 'skills'):
                    if key in meta:
                        match[key] = meta[key]
            matches.append(match)

        return matches

    def search_all(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across multiple collections."""
        categories = categories or COLLECTION_NAMES
        results = {}
        for category in categories:
            try:
                results[category] = self.search(category, query, top_k=top_k, where=where)
            except ChromaServiceError:
                results[category] = []
        return results

    def count(self, category: str) -> int:
        """Return number of documents in a collection."""
        try:
            collection = self.get_collection(category, create=False)
            return collection.count()
        except Exception:
            return 0

    def stats(self) -> Dict[str, int]:
        """Return document counts for all collections."""
        return {name: self.count(name) for name in COLLECTION_NAMES}

    @staticmethod
    def _build_metadata(opp: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten opportunity metadata for ChromaDB."""
        skills = opp.get('required_skills', [])
        if isinstance(skills, list):
            skills = ', '.join(skills)

        return {
            'id': opp.get('id', ''),
            'category': opp.get('category', ''),
            'country': opp.get('location', ''),
            'degree': opp.get('degree_level', ''),
            'deadline': opp.get('deadline_iso', opp.get('deadline', '')),
            'organization': opp.get('organization', ''),
            'url': opp.get('url', ''),
            'skills': skills,
            'title': opp.get('title', ''),
        }


chroma_service = ChromaService()
