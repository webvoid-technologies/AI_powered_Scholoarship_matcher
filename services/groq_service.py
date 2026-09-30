import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests
from config import Config


class GroqServiceError(Exception):
    pass


class GroqService:
    """Client for the Groq LLM API with retries, JSON extraction, and mock fallback."""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.api_key = self.config.GROQ_API_KEY
        self.model = self.config.GROQ_MODEL
        self.api_url = self.config.GROQ_API_URL
        self.timeout = self.config.REQUEST_TIMEOUT
        self.max_tokens = self.config.MAX_TOKENS
        self.temperature = self.config.TEMPERATURE

    def _load_prompt(self, prompt_name: str, **kwargs) -> str:
        path = os.path.join('prompts', f'{prompt_name}.txt')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            raise GroqServiceError(f'Prompt template not found: {path}')

        # Replace placeholders safely
        for key, value in kwargs.items():
            placeholder = '{' + key + '}'
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            elif value is None:
                value = ''
            template = template.replace(placeholder, str(value))

        # Remove any unreplaced simple placeholders but keep JSON example braces
        template = re.sub(r'(?<!\{)\{[A-Za-z_][A-Za-z0-9_]*\}(?!\})', '', template)
        return template

    def _call_api(self, prompt: str, retries: int = 2) -> str:
        if not self.api_key:
            raise GroqServiceError('GROQ_API_KEY is not configured.')

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You are a helpful education and career advisor AI for students. '
                        'Return only valid JSON matching the requested schema. '
                        'Do not include Markdown code fences or explanations outside the JSON.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

        last_exception = None
        for attempt in range(retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content']
            except requests.exceptions.Timeout:
                last_exception = GroqServiceError('Groq API request timed out.')
            except requests.exceptions.HTTPError as e:
                msg = f'Groq API error: {e.response.status_code}'
                try:
                    err = e.response.json()
                    msg += f' - {err.get("error", {}).get("message", "")}'
                except Exception:
                    pass
                raise GroqServiceError(msg)
            except (KeyError, IndexError) as e:
                raise GroqServiceError(f'Unexpected Groq API response format: {e}')
            except Exception as e:
                last_exception = GroqServiceError(f'Groq API call failed: {str(e)}')

            if attempt < retries:
                time.sleep(1.5 ** attempt)

        raise last_exception or GroqServiceError('Groq API call failed.')

    def _extract_json(self, content: str) -> Any:
        content = content.strip()

        # Strip Markdown fences
        if content.startswith('```'):
            lines = content.splitlines()
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            content = '\n'.join(lines).strip()

        # Try to find JSON object/array if extra text exists
        for pattern in (r'\{[\s\S]*\}', r'\[[\s\S]*\]'):
            match = re.search(pattern, content)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise GroqServiceError(f'Failed to parse JSON from model output: {e}')

    def generate(self, prompt_name: str, **kwargs) -> Dict[str, Any]:
        prompt = self._load_prompt(prompt_name, **kwargs)
        content = self._call_api(prompt)
        result = self._extract_json(content)
        if not isinstance(result, dict):
            result = {'data': result}
        result.setdefault('success', True)
        return result

    def generate_mock(self, prompt_name: str, **kwargs) -> Dict[str, Any]:
        """Return realistic sample data when the API key is unavailable."""
        skills = kwargs.get('skills', ['Python', 'Web Development'])
        interests = kwargs.get('interests', ['AI/ML', 'Competitive Programming'])
        goal = kwargs.get('career_goal', 'Job')
        context = kwargs.get('context', '')

        if prompt_name == 'profile_prompt':
            return {
                'success': True,
                'mock': True,
                'summary': f"A motivated {kwargs.get('year_of_study', 'Final Year')} {kwargs.get('degree_branch', 'B.Tech CSE')} student with skills in {', '.join(skills)} aiming for {goal}.",
                'strengths': skills[:3] or ['Programming', 'Problem solving', 'Communication'],
                'suggested_focus_areas': interests[:2] or ['AI/ML', 'Cloud Computing'],
                'recommended_opportunity_types': ['Internships', 'Hackathons', 'Certifications']
            }

        if prompt_name == 'scholarship_prompt':
            return {
                'success': True,
                'mock': True,
                'matches': [
                    {
                        'name': 'AICTE Pragati Scholarship',
                        'category': 'Government',
                        'match_percentage': 92,
                        'eligibility': 'Female students in technical diploma/degree programs with family income below INR 8 lakh.',
                        'benefits': 'Tuition fee up to INR 30,000 and INR 2,000 monthly incidentals.',
                        'deadline': '31 December 2026',
                        'why_it_matches': 'Aligns with Indian technical education and supports women in engineering.',
                        'tips': 'Keep income certificate and college bonafide ready.',
                        'url': 'https://www.aicte-india.org/schemes/students-development-schemes'
                    },
                    {
                        'name': 'Google Generation Scholarship APAC',
                        'category': 'Private',
                        'match_percentage': 88,
                        'eligibility': 'Women in computer science demonstrating academic excellence and leadership.',
                        'benefits': 'USD 1,000 award and access to Google community events.',
                        'deadline': '30 April 2026',
                        'why_it_matches': 'Supports women pursuing CS/IT degrees across Asia-Pacific.',
                        'tips': 'Highlight leadership in tech clubs and open-source contributions.',
                        'url': 'https://buildyourfuture.withgoogle.com/scholarships'
                    }
                ]
            }

        if prompt_name == 'internship_prompt':
            return {
                'success': True,
                'mock': True,
                'matches': [
                    {
                        'role': 'Software Engineering Intern',
                        'company': 'Webvoid Technologies',
                        'required_skills': skills,
                        'duration': '3-6 months',
                        'eligibility': 'Pursuing UG/PG in CS/IT with strong programming fundamentals.',
                        'learning_outcomes': 'Full-stack development, CI/CD, agile practices.',
                        'why_it_matches': 'Matches your programming skills and interest in web development.',
                        'preparation_roadmap': 'Build a portfolio project, practice DSA, learn Git workflows.',
                        'tips': 'Showcase a Flask or React project on GitHub.',
                        'url': 'https://webvoidtechnologies.com/careers'
                    },
                    {
                        'role': 'Google Summer of Code Contributor',
                        'company': 'Google / Open Source',
                        'required_skills': skills + ['Open Source', 'Git/GitHub'],
                        'duration': '3 months',
                        'eligibility': 'Students 18+ comfortable with open-source contribution.',
                        'learning_outcomes': 'Global open-source collaboration and real-world coding.',
                        'why_it_matches': 'Great for students who enjoy building and collaborating on open-source software.',
                        'preparation_roadmap': 'Explore GSoC organizations, solve good-first-issues, draft a proposal.',
                        'tips': 'Start contributing to projects at least 2 months before applications.',
                        'url': 'https://summerofcode.withgoogle.com/'
                    }
                ]
            }

        if prompt_name == 'hackathon_prompt':
            return {
                'success': True,
                'mock': True,
                'matches': [
                    {
                        'name': 'Smart India Hackathon',
                        'type': 'Hackathon',
                        'theme': 'Open Innovation / Software',
                        'eligibility': 'Teams of 6 students from Indian colleges.',
                        'required_skills': skills + interests,
                        'team_size': '6',
                        'preparation_tips': 'Form team, select problem statement, prototype MVP, practice pitch.',
                        'why_it_matches': 'India\'s largest hackathon with software problem statements matching your skills.',
                        'official_link': 'https://sih.gov.in/'
                    },
                    {
                        'name': 'Microsoft Imagine Cup',
                        'type': 'Innovation Challenge',
                        'theme': 'AI for Good',
                        'eligibility': 'Students aged 16+ building technology for social impact.',
                        'required_skills': ['Azure', 'AI/ML'] + skills,
                        'team_size': '1-4',
                        'preparation_tips': 'Validate problem, build MVP, create pitch deck, test on Azure.',
                        'why_it_matches': 'Matches interest in {interests} and desire to build impactful solutions.'.format(interests=', '.join(interests)),
                        'official_link': 'https://imaginecup.microsoft.com/'
                    }
                ]
            }

        if prompt_name == 'fellowship_prompt':
            return {
                'success': True,
                'mock': True,
                'matches': [
                    {
                        'name': 'MITACS Globalink Research Internship',
                        'type': 'Research Internship',
                        'eligibility': 'UG students with research interest and strong academics.',
                        'benefits': 'Travel, stipend, and international research experience.',
                        'why_it_matches': 'Ideal for students exploring research and international exposure.',
                        'tips': 'Get recommendation letters and align project with your interests.',
                        'official_link': 'https://www.mitacs.ca/en/programs/globalink/globalink-research-internship'
                    }
                ]
            }

        if prompt_name == 'certification_prompt':
            return {
                'success': True,
                'mock': True,
                'roadmap': [
                    {
                        'level': 'Beginner',
                        'name': 'Python for Everybody (Coursera / University of Michigan)',
                        'provider': 'University of Michigan',
                        'skills_gained': ['Python', 'Data Structures', 'Web Scraping'],
                        'learning_path': 'Programming basics -> Data structures -> APIs',
                        'duration': '2-3 months',
                        'tips': 'Complete all assignments and build small CLI tools.',
                        'url': 'https://www.coursera.org/specializations/python'
                    },
                    {
                        'level': 'Intermediate',
                        'name': 'AWS Certified Cloud Practitioner',
                        'provider': 'Amazon Web Services',
                        'skills_gained': ['Cloud', 'AWS', 'Architecture'],
                        'learning_path': 'Cloud fundamentals -> Core services -> Practice exams',
                        'duration': '1-2 months',
                        'tips': 'Use free tier labs and official practice questions.',
                        'url': 'https://aws.amazon.com/certification/certified-cloud-practitioner/'
                    }
                ]
            }

        if prompt_name == 'skill_gap_prompt':
            return {
                'success': True,
                'mock': True,
                'analysis': {
                    'career_goal': goal,
                    'current_skills': skills,
                    'missing_skills': ['System Design', 'SQL Optimization', 'Docker'],
                    'recommended_technologies': ['Docker', 'Kubernetes', 'Redis', 'PostgreSQL'],
                    'suggested_projects': [
                        {'title': 'Build a scalable URL shortener', 'description': 'Practice system design and databases.', 'technologies': ['Redis', 'PostgreSQL']},
                        {'title': 'Create a real-time analytics dashboard', 'description': 'Learn streaming and visualization.', 'technologies': ['Kafka', 'React', 'D3.js']}
                    ],
                    'resume_tips': ['Quantify impact and include GitHub links for every project.', 'Add metrics like load time reductions or user counts.', 'Tailor resume keywords to each job description.']
                }
            }

        if prompt_name == 'career_report_prompt':
            return {
                'success': True,
                'mock': True,
                'report': {
                    'summary': f'Profile aligned with {goal} goal. Strong foundation in {", ".join(skills)}.',
                    'top_scholarships': ['AICTE Pragati Scholarship', 'Google Generation Scholarship APAC'],
                    'top_internships': ['Software Engineering Intern at Webvoid Technologies', 'Google Summer of Code'],
                    'top_hackathons': ['Smart India Hackathon', 'Microsoft Imagine Cup'],
                    'top_fellowships': ['MITACS Globalink Research Internship'],
                    'top_certifications': ['Python for Everybody', 'AWS Certified Cloud Practitioner'],
                    'career_roadmap': [
                        {'stage': 'Foundation', 'duration': '0-6 months', 'actions': skills[:3]},
                        {'stage': 'Skill Building', 'duration': '6-12 months', 'actions': interests[:3]},
                        {'stage': 'Specialization', 'duration': '1-2 years', 'actions': [goal]}
                    ],
                    'application_strategy': 'Apply early, tailor resume per role, network on LinkedIn, and build a public portfolio.',
                    'next_steps': ['Create a GitHub portfolio', 'Earn one cloud certification', 'Apply to 5 internships this month']
                }
            }

        if prompt_name == 'chat_prompt':
            return {
                'success': True,
                'mock': True,
                'answer': (
                    'I found some relevant opportunities for you. Based on your profile, '
                    'you may be eligible for government scholarships like AICTE Pragati and '
                    'private scholarships like Google Generation Scholarship APAC. '
                    'For internships, consider Webvoid Technologies and Google Summer of Code. '
                    'Would you like details on a specific category?'
                ),
                'follow_up_questions': [
                    'Show scholarships for women in engineering',
                    'Find remote internships for Python developers',
                    'What hackathons are happening this year?'
                ]
            }

        return {'success': True, 'mock': True, 'data': []}


groq_service = GroqService()
