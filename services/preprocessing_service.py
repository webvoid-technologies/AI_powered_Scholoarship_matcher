"""Data cleaning and preprocessing utilities for scraped opportunities."""

import json
import re
from datetime import datetime
from html import unescape
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


class PreprocessingServiceError(Exception):
    pass


class PreprocessingService:
    """Clean, normalize, and prepare opportunity data for embedding."""

    def __init__(self):
        self.date_patterns = [
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', '%d/%m/%y'),
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', '%d/%m/%Y'),
            (r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', '%Y-%m-%d'),
            (r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', '%d %B %Y'),
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})\b', '%B %d, %Y'),
        ]

    def clean_html(self, raw_html: str) -> str:
        """Remove HTML tags and unescape HTML entities."""
        if not raw_html:
            return ''
        text = BeautifulSoup(raw_html, 'html.parser').get_text(separator=' ')
        return unescape(text)

    def normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace characters into single spaces."""
        if not text:
            return ''
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def standardize_date(self, date_str: str) -> str:
        """Attempt to convert a date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return ''
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        for pattern, fmt in self.date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    parsed = datetime.strptime(match.group(0), fmt)
                    if parsed.year < 100:
                        parsed = parsed.replace(year=parsed.year + 2000)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return date_str

    def build_document(self, opportunity: Dict[str, Any]) -> str:
        """Build a single text document from structured opportunity fields."""
        parts = [
            f"Title: {opportunity.get('title', '')}",
            f"Category: {opportunity.get('category', '')}",
            f"Organization: {opportunity.get('organization', '')}",
            f"Description: {opportunity.get('description', '')}",
        ]

        if opportunity.get('degree_level'):
            parts.append(f"Degree Level: {opportunity.get('degree_level')}")
        if opportunity.get('eligibility'):
            parts.append(f"Eligibility: {opportunity.get('eligibility')}")
        if opportunity.get('benefits'):
            parts.append(f"Benefits: {opportunity.get('benefits')}")
        if opportunity.get('deadline'):
            parts.append(f"Deadline: {opportunity.get('deadline')}")
        if opportunity.get('location'):
            parts.append(f"Location: {opportunity.get('location')}")
        if opportunity.get('required_skills'):
            skills = opportunity.get('required_skills')
            if isinstance(skills, list):
                skills = ', '.join(skills)
            parts.append(f"Required Skills: {skills}")
        if opportunity.get('url'):
            parts.append(f"URL: {opportunity.get('url')}")

        return self.normalize_whitespace(' '.join(parts))

    def clean_opportunity(self, opportunity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and normalize a single opportunity record."""
        if not opportunity or not opportunity.get('title'):
            return None

        cleaned = {}
        for key, value in opportunity.items():
            if isinstance(value, str):
                cleaned[key] = self.normalize_whitespace(self.clean_html(value))
            elif isinstance(value, list):
                cleaned[key] = [self.normalize_whitespace(self.clean_html(v)) if isinstance(v, str) else v for v in value]
            else:
                cleaned[key] = value

        if cleaned.get('deadline'):
            cleaned['deadline_iso'] = self.standardize_date(cleaned['deadline'])

        cleaned['document'] = self.build_document(cleaned)
        cleaned.setdefault('id', self._generate_id(cleaned))
        return cleaned

    def remove_duplicates(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate opportunities based on normalized title + organization."""
        seen = set()
        unique = []
        for opp in opportunities:
            key = (
                opp.get('title', '').lower().strip(),
                opp.get('organization', '').lower().strip(),
                opp.get('category', '').lower().strip()
            )
            if key not in seen:
                seen.add(key)
                unique.append(opp)
        return unique

    def process(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Process raw scraped data into clean, embedded-ready records."""
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError as exc:
                raise PreprocessingServiceError(f'Invalid JSON input: {exc}')

        if isinstance(raw_data, dict):
            raw_data = raw_data.get('opportunities', [raw_data])

        if not isinstance(raw_data, list):
            raise PreprocessingServiceError('Expected a list of opportunities or a dict containing "opportunities".')

        cleaned = []
        for opp in raw_data:
            processed = self.clean_opportunity(opp)
            if processed:
                cleaned.append(processed)

        return self.remove_duplicates(cleaned)

    @staticmethod
    def _generate_id(opportunity: Dict[str, Any]) -> str:
        """Generate a deterministic ID from key fields."""
        base = f"{opportunity.get('category', 'opp')}-{opportunity.get('organization', 'org')}-{opportunity.get('title', 'title')}"
        normalized = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
        return normalized[:120]


preprocessing_service = PreprocessingService()
