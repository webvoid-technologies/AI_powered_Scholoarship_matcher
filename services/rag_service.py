"""Retrieval-Augmented Generation (RAG) service for opportunity matching."""

import os
from typing import Any, Dict, List, Optional

from config import Config
from services.chroma_service import COLLECTION_NAMES, ChromaService, chroma_service
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService


class RAGServiceError(Exception):
    pass


class RAGService:
    """Combine ChromaDB retrieval with Groq LLM generation."""

    def __init__(
        self,
        config: Config = None,
        chroma_service: ChromaService = None,
        embedding_service: EmbeddingService = None,
        groq_service: GroqService = None
    ):
        self.config = config or Config()
        self.chroma = chroma_service or ChromaService()
        self.embedder = embedding_service or EmbeddingService()
        self.groq = groq_service or GroqService()
        self.default_top_k = int(os.environ.get('RAG_TOP_K', '5'))

    def _build_query(self, prompt_name: str, **kwargs) -> str:
        """Build a semantic search query from user profile and/or natural language."""
        if 'query' in kwargs and kwargs['query']:
            return str(kwargs['query'])

        parts = []
        if 'career_goal' in kwargs:
            parts.append(str(kwargs['career_goal']))
        if 'degree_branch' in kwargs:
            parts.append(str(kwargs['degree_branch']))
        if 'year_of_study' in kwargs:
            parts.append(f"{kwargs['year_of_study']} student")
        if 'location' in kwargs:
            parts.append(f"based in {kwargs['location']}")
        if 'skills' in kwargs and kwargs['skills']:
            skills = kwargs['skills']
            if isinstance(skills, list):
                skills = ', '.join(skills)
            parts.append(f"skills: {skills}")
        if 'interests' in kwargs and kwargs['interests']:
            interests = kwargs['interests']
            if isinstance(interests, list):
                interests = ', '.join(interests)
            parts.append(f"interests: {interests}")
        if 'education_level' in kwargs:
            parts.append(str(kwargs['education_level']))

        query = ' '.join(parts)

        # Tailor query by module
        module_keywords = {
            'scholarship_prompt': 'scholarships grants financial aid funding',
            'internship_prompt': 'internships industrial training work experience',
            'hackathon_prompt': 'hackathons coding competitions innovation challenges',
            'fellowship_prompt': 'fellowships research programs exchange opportunities',
            'certification_prompt': 'certifications courses online learning skill badges',
            'skill_gap_prompt': 'career skills roadmap project recommendations',
            'career_report_prompt': 'career roadmap scholarships internships opportunities'
        }
        keyword = module_keywords.get(prompt_name, '')
        if keyword:
            query = f"{keyword} for {query}"

        return query

    def _build_context(self, matches: List[Dict[str, Any]]) -> str:
        """Format retrieved matches into context for the LLM."""
        if not matches:
            return 'No matching opportunities found in the database.'

        context_parts = []
        for idx, match in enumerate(matches, 1):
            lines = [f"Opportunity {idx} (Match Score: {match.get('score', 0)}%):"]
            doc = match.get('document', '').strip()
            if doc:
                lines.append(doc)
            url = match.get('url') or match.get('official_link')
            if url:
                lines.append(f"URL: {url}")
            context_parts.append('\n'.join(lines))

        return '\n\n---\n\n'.join(context_parts)

    def retrieve(
        self,
        prompt_name: str,
        categories: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve relevant documents from ChromaDB."""
        query = self._build_query(prompt_name, **kwargs)
        categories = categories or self._categories_for_prompt(prompt_name)
        top_k = top_k or self.default_top_k

        all_matches = {}
        for category in categories:
            try:
                matches = self.chroma.search(category, query, top_k=top_k, where=where)
                all_matches[category] = matches
            except Exception:
                all_matches[category] = []
        return all_matches

    def generate(
        self,
        prompt_name: str,
        profile: Dict[str, Any],
        query_override: Optional[str] = None,
        categories: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run the full RAG pipeline: retrieve context + call LLM."""
        search_kwargs = dict(profile)
        if query_override:
            search_kwargs['query'] = query_override

        retrieved = self.retrieve(
            prompt_name,
            categories=categories,
            top_k=top_k,
            where=where,
            **search_kwargs
        )

        # Flatten and sort matches across categories
        flat_matches = []
        for category, matches in retrieved.items():
            for match in matches:
                match['category_collection'] = category
                flat_matches.append(match)
        flat_matches.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_matches = flat_matches[:top_k or self.default_top_k]

        context = self._build_context(top_matches)

        # Prepare prompt kwargs
        prompt_kwargs = {
            'context': context,
            'retrieved_count': len(top_matches),
            **profile
        }
        if query_override:
            prompt_kwargs['user_question'] = query_override

        result = self.groq.generate(prompt_name, **prompt_kwargs)
        result['retrieved'] = top_matches
        result['query'] = query_override or self._build_query(prompt_name, **profile)
        return result

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        profile: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """RAG-powered chatbot response."""
        history = history or []
        profile = profile or {}

        search_kwargs = dict(profile)
        search_kwargs['query'] = message
        retrieved = self.retrieve(
            'chat_prompt',
            categories=categories or COLLECTION_NAMES,
            top_k=top_k or self.default_top_k,
            **search_kwargs
        )

        flat_matches = []
        for category, matches in retrieved.items():
            for match in matches:
                match['category_collection'] = category
                flat_matches.append(match)
        flat_matches.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_matches = flat_matches[:top_k or self.default_top_k]

        context = self._build_context(top_matches)
        prompt_kwargs = {
            'context': context,
            'user_question': message,
            'conversation_history': self._format_history(history),
            **profile
        }

        result = self.groq.generate('chat_prompt', **prompt_kwargs)
        result['retrieved'] = top_matches
        result['query'] = message
        return result

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for the prompt."""
        formatted = []
        for turn in history[-6:]:
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            formatted.append(f"{role.capitalize()}: {content}")
        return '\n'.join(formatted)

    @staticmethod
    def _categories_for_prompt(prompt_name: str) -> List[str]:
        mapping = {
            'scholarship_prompt': ['scholarships'],
            'internship_prompt': ['internships'],
            'hackathon_prompt': ['hackathons'],
            'fellowship_prompt': ['fellowships'],
            'certification_prompt': ['certifications'],
            'career_report_prompt': COLLECTION_NAMES,
            'skill_gap_prompt': COLLECTION_NAMES,
        }
        return mapping.get(prompt_name, COLLECTION_NAMES)


rag_service = RAGService()
