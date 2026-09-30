"""Web scraping service for scholarship and opportunity collection."""

import json
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
import trafilatura
from bs4 import BeautifulSoup

from services.preprocessing_service import preprocessing_service


class ScraperServiceError(Exception):
    pass


class BaseOpportunityScraper(ABC):
    """Abstract base class for opportunity scrapers."""

    def __init__(self, name: str, base_url: str, category: str):
        self.name = name
        self.base_url = base_url
        self.category = category
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        }
        self.timeout = 30

    def fetch(self, url: str) -> Optional[str]:
        """Fetch raw HTML from a URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise ScraperServiceError(f'Failed to fetch {url}: {exc}') from exc

    @abstractmethod
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML and return a list of opportunity dictionaries."""
        pass

    def scrape(self) -> List[Dict[str, Any]]:
        """Run the scraper and return cleaned opportunities."""
        html = self.fetch(self.base_url)
        opportunities = self.parse(html)
        for opp in opportunities:
            opp.setdefault('category', self.category)
            opp.setdefault('source', self.name)
            opp.setdefault('source_url', self.base_url)
        return preprocessing_service.process(opportunities)


class SampleDataScraper(BaseOpportunityScraper):
    """Scraper that returns curated sample data instead of live scraping."""

    def __init__(self, category: str, sample_data: List[Dict[str, Any]]):
        super().__init__(name='SampleData', base_url='https://example.com', category=category)
        self.sample_data = sample_data

    def fetch(self, url: str) -> str:
        return ''

    def parse(self, html: str) -> List[Dict[str, Any]]:
        return [dict(item) for item in self.sample_data]


class BuiltinSampleScraper(BaseOpportunityScraper):
    """Scraper that returns built-in sample opportunities."""

    def __init__(self):
        super().__init__(name='BuiltinSample', base_url='https://webvoidtechnologies.com/opportunities', category='mixed')

    def fetch(self, url: str) -> str:
        return ''

    def parse(self, html: str) -> List[Dict[str, Any]]:
        return load_builtin_samples()


class GenericHTMLScraper(BaseOpportunityScraper):
    """Generic fallback scraper that extracts headings and links."""

    def __init__(self, name: str, base_url: str, category: str):
        super().__init__(name, base_url, category)

    def parse(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        opportunities = []
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            href = link['href']
            if href.startswith('/'):
                href = self.base_url.rstrip('/') + href
            elif not href.startswith('http'):
                href = self.base_url.rstrip('/') + '/' + href
            opportunities.append({
                'title': title,
                'description': title,
                'url': href,
                'organization': self.name,
                'category': self.category
            })
        return opportunities


class TrafilaturaScraper(BaseOpportunityScraper):
    """Scraper using trafilatura for deep text extraction from article pages."""

    def __init__(self, name: str, base_url: str, category: str):
        super().__init__(name, base_url, category)

    def fetch(self, url: str) -> Optional[str]:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ScraperServiceError(f'Trafilatura failed to fetch {url}')
        return downloaded

    def parse(self, html: str) -> List[Dict[str, Any]]:
        text = trafilatura.extract(
            html, include_links=True, include_tables=True, favor_recall=True
        )
        if not text or len(text) < 100:
            return []
        return self._extract_opportunities_from_text(text)

    def _extract_opportunities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse unstructured text into opportunity records using heuristics."""
        opportunities = []
        # Split text into sections by common patterns (numbered items, headings)
        sections = re.split(
            r'\n(?=\d+[\.\)]\s|#{1,3}\s|[A-Z][A-Za-z\s\-&]+(?:Scholarship|Internship|Hackathon|Fellowship|Certificate|Certification|Program|Course|Grant|Award|Scheme))',
            text
        )

        for section in sections:
            section = section.strip()
            if len(section) < 50:
                continue

            lines = section.split('\n')
            title_line = lines[0].strip()
            # Clean title of numbering and markdown
            title_line = re.sub(r'^[\d\.\)\-\*#]+\s*', '', title_line).strip()
            if not title_line or len(title_line) < 5 or len(title_line) > 200:
                continue

            # Skip non-opportunity text
            skip_words = ['table of contents', 'how to apply', 'frequently asked', 'faq',
                          'conclusion', 'introduction', 'disclaimer', 'also read']
            if any(sw in title_line.lower() for sw in skip_words):
                continue

            body = '\n'.join(lines[1:]).strip()

            # Extract fields from body text
            opp = {
                'title': title_line,
                'category': self.category,
                'source': self.name,
                'source_url': self.base_url,
            }

            # Extract eligibility
            elig_match = re.search(r'(?:eligibility|who can apply)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if elig_match:
                opp['eligibility'] = elig_match.group(1).strip()

            # Extract benefits/amount
            ben_match = re.search(r'(?:benefits?|amount|award|stipend|prize)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if ben_match:
                opp['benefits'] = ben_match.group(1).strip()

            # Extract deadline
            dl_match = re.search(r'(?:deadline|last date|apply by|due date)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if dl_match:
                opp['deadline'] = dl_match.group(1).strip()

            # Extract duration
            dur_match = re.search(r'(?:duration)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if dur_match:
                opp['duration'] = dur_match.group(1).strip()

            # Extract organization
            org_match = re.search(r'(?:organiz|organis|provider|offered by|funded by|by)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if org_match:
                opp['organization'] = org_match.group(1).strip()[:100]
            else:
                opp['organization'] = self.name

            # Extract URL from body
            url_match = re.search(r'(https?://[^\s\)]+)', body)
            if url_match:
                opp['url'] = url_match.group(1)
            else:
                opp['url'] = self.base_url

            # Build description from full section text
            opp['description'] = (body[:500] if body else title_line).strip()

            # Extract location
            loc_match = re.search(r'(?:location|country|region|format)[:\s]*(.+?)(?:\n|$)', body, re.I)
            if loc_match:
                opp['location'] = loc_match.group(1).strip()

            # Extract skills from keywords
            skill_keywords = re.findall(
                r'\b(Python|Java|JavaScript|C\+\+|SQL|Machine Learning|AI|ML|Data Science|'
                r'Cloud|AWS|Azure|React|Node\.js|Docker|Git|Linux|Research|Leadership|'
                r'Communication|Teamwork|Web Development|Mobile|Android|iOS|Blockchain|'
                r'Deep Learning|NLP|Computer Vision|DevOps|Kubernetes|TensorFlow|PyTorch)\b',
                body, re.I
            )
            if skill_keywords:
                opp['required_skills'] = list(set(s.title() for s in skill_keywords))

            opportunities.append(opp)

        return opportunities


# ---------- Real web sources per category ----------

SCRAPE_SOURCES = {
    'scholarships': [
        ('Buddy4Study', 'https://www.buddy4study.com/article/scholarships-for-engineering-students'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/scholarships-for-women-in-india'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/scholarships-for-mba-students'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/national-scholarship-portal'),
        ('OpportunityCell', 'https://opportunitycell.com/category/scholarships/'),
    ],
    'internships': [
        ('OpportunityCell', 'https://opportunitycell.com/category/internships/'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/internships-for-engineering-students'),
    ],
    'hackathons': [
        ('OpportunityCell', 'https://opportunitycell.com/category/competitions/'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/hackathons-for-students'),
    ],
    'fellowships': [
        ('OpportunityCell', 'https://opportunitycell.com/fellowships/'),
        ('Buddy4Study', 'https://www.buddy4study.com/article/fellowships-in-india'),
    ],
    'certifications': [
        ('Buddy4Study', 'https://www.buddy4study.com/article/free-online-courses-with-certificates'),
        ('Coursera', 'https://www.coursera.org/collections/popular-free-courses'),
    ],
}


def load_builtin_samples() -> List[Dict[str, Any]]:
    """Load a diverse built-in opportunity dataset."""
    return [
        # Scholarships
        {
            "title": "AICTE Pragati Scholarship Scheme",
            "organization": "AICTE, Ministry of Education, India",
            "category": "scholarships",
            "degree_level": "Diploma / UG",
            "eligibility": "Female students enrolled in AICTE-approved technical diploma or degree programs with family income below INR 8 lakh per annum.",
            "benefits": "Tuition fee reimbursement up to INR 30,000 and INR 2,000 per month incidentals for 10 months.",
            "deadline": "31 December 2026",
            "location": "India",
            "required_skills": ["Technical diploma", "Engineering", "Academic merit"],
            "description": "Government scholarship for girl students pursuing technical education in India.",
            "url": "https://www.aicte-india.org/schemes/students-development-schemes"
        },
        {
            "title": "Google Generation Scholarship APAC",
            "organization": "Google",
            "category": "scholarships",
            "degree_level": "UG / PG",
            "eligibility": "Women in computer science and related technical fields demonstrating leadership and academic excellence.",
            "benefits": "Financial award, retreat invitation, and access to Google community and mentorship.",
            "deadline": "30 April 2026",
            "location": "Asia-Pacific",
            "required_skills": ["Computer Science", "Leadership", "Academic excellence"],
            "description": "Scholarship supporting women pursuing degrees in computer science in Asia-Pacific.",
            "url": "https://buildyourfuture.withgoogle.com/scholarships"
        },
        {
            "title": "Adobe India Women in Technology Scholarship",
            "organization": "Adobe",
            "category": "scholarships",
            "degree_level": "UG",
            "eligibility": "Women students in technical fields in India with strong academic record and project work.",
            "benefits": "Tuition funding, internship interview opportunity, and mentorship by Adobe leaders.",
            "deadline": "31 August 2026",
            "location": "India",
            "required_skills": ["Software Engineering", "Computer Science", "Portfolio projects"],
            "description": "Adobe scholarship to empower women technologists in India.",
            "url": "https://www.adobe.com/in/creativecloud/photography/discover/women-in-technology.html"
        },
        {
            "title": "Tata Capital Pankh Scholarship",
            "organization": "Tata Capital",
            "category": "scholarships",
            "degree_level": "UG / PG",
            "eligibility": "Students from economically weaker sections enrolled in undergraduate or postgraduate courses.",
            "benefits": "Financial assistance up to INR 20,000 per annum for tuition and educational expenses.",
            "deadline": "31 March 2026",
            "location": "India",
            "required_skills": ["Academic continuity", "Financial need documentation"],
            "description": "Need-based scholarship program supporting higher education for underprivileged students.",
            "url": "https://www.buddy4study.com/page/tata-capital-pankh-scholarship"
        },
        {
            "title": "Fulbright-Nehru Master's Fellowship",
            "organization": "USIEF / US Government",
            "category": "scholarships",
            "degree_level": "PG",
            "eligibility": "Outstanding Indian students with strong academic background, leadership, and community service for master's study in the US.",
            "benefits": "Full tuition, living stipend, airfare, health insurance, and visa support.",
            "deadline": "15 July 2026",
            "location": "United States",
            "required_skills": ["Research aptitude", "Leadership", "English proficiency"],
            "description": "Prestigious US-India educational exchange fellowship for master's level study.",
            "url": "https://www.usief.org.in/Fulbright-Nehru-Master-s-Fellowships.aspx"
        },
        {
            "title": "Inlaks Shivdasani Foundation Scholarship",
            "organization": "Inlaks Foundation",
            "category": "scholarships",
            "degree_level": "PG",
            "eligibility": "Indian students under 30 admitted to top universities in Europe, UK, or US for full-time master's.",
            "benefits": "Full funding covering tuition, living expenses, and one-way travel.",
            "deadline": "31 March 2026",
            "location": "International",
            "required_skills": ["Academic excellence", "Admissions offer", "Research proposal"],
            "description": "Full scholarship for Indian students pursuing postgraduate education abroad.",
            "url": "https://www.inlaksfoundation.org/scholarships/"
        },

        # Internships
        {
            "title": "Webvoid Technologies Software Engineering Internship",
            "organization": "Webvoid Technologies",
            "category": "internships",
            "degree_level": "UG / PG",
            "eligibility": "Students pursuing B.Tech, M.Tech, or MCA in CS/IT with strong programming fundamentals.",
            "benefits": "Hands-on full-stack project experience, mentorship, certificate, and stipend.",
            "deadline": "Rolling",
            "location": "Remote / Hybrid",
            "required_skills": ["Python", "Flask", "JavaScript", "SQL", "Git"],
            "description": "Full-stack development internship building production AI-powered web applications.",
            "url": "https://webvoidtechnologies.com/careers"
        },
        {
            "title": "Google Summer of Code",
            "organization": "Google / Open Source",
            "category": "internships",
            "degree_level": "UG / PG",
            "eligibility": "Students 18 or older comfortable with open-source contribution and coding.",
            "benefits": "Stipend USD 1,500-6,600 depending on region, mentorship, and global open-source experience.",
            "deadline": "10 April 2026",
            "location": "Global (Remote)",
            "required_skills": ["Open Source", "Git/GitHub", "Programming", "Communication"],
            "description": "Global program pairing student developers with open-source organizations.",
            "url": "https://summerofcode.withgoogle.com/"
        },
        {
            "title": "Microsoft Research Internship India",
            "organization": "Microsoft Research",
            "category": "internships",
            "degree_level": "UG / PG",
            "eligibility": "Students with strong academics and research interest in systems, AI, or human-computer interaction.",
            "benefits": "Industry research exposure, mentorship, competitive stipend, and pre-placement interviews.",
            "deadline": "Rolling",
            "location": "India",
            "required_skills": ["Algorithms", "Machine Learning", "Research writing", "C++/Python"],
            "description": "Research internship at Microsoft Research India labs across Bangalore and Hyderabad.",
            "url": "https://www.microsoft.com/en-us/research/careers/"
        },
        {
            "title": "Amazon SDE Internship",
            "organization": "Amazon",
            "category": "internships",
            "degree_level": "UG / PG",
            "eligibility": "Computer science students with strong data structures, algorithms, and system design skills.",
            "benefits": "Competitive stipend, return offer potential, mentorship, and AWS learning credits.",
            "deadline": "Rolling",
            "location": "India / International",
            "required_skills": ["Data Structures", "Algorithms", "System Design", "Java/Python"],
            "description": "Software Development Engineer internship at Amazon working on large-scale distributed systems.",
            "url": "https://www.amazon.jobs/content/en/teams/internships"
        },

        # Hackathons
        {
            "title": "Smart India Hackathon",
            "organization": "Ministry of Education, India",
            "category": "hackathons",
            "degree_level": "UG / PG",
            "eligibility": "Teams of 6 students from Indian colleges; one female member mandatory.",
            "benefits": "Cash prizes up to INR 1 lakh, mentorship, incubation support, and national recognition.",
            "deadline": "15 January 2026",
            "location": "India",
            "required_skills": ["Problem solving", "Teamwork", "Prototyping", "Pitching"],
            "description": "World's largest open innovation model solving government and industry problem statements.",
            "url": "https://sih.gov.in/"
        },
        {
            "title": "Microsoft Imagine Cup",
            "organization": "Microsoft",
            "category": "hackathons",
            "degree_level": "UG / PG",
            "eligibility": "Students aged 16+ building technology solutions for social impact.",
            "benefits": "Global finals, USD 100,000 grand prize, Azure credits, and mentorship.",
            "deadline": "1 February 2026",
            "location": "Global",
            "required_skills": ["Azure", "AI/ML", "Cloud", "Presentation"],
            "description": "Global student technology competition using Microsoft tools to solve real-world challenges.",
            "url": "https://imaginecup.microsoft.com/"
        },
        {
            "title": "ETHIndia Hackathon",
            "organization": "ETHGlobal",
            "category": "hackathons",
            "degree_level": "UG / PG",
            "eligibility": "Developers, designers, and builders interested in Ethereum and Web3.",
            "benefits": "Bounties up to USD 50,000+, networking, and grants for promising projects.",
            "deadline": "1 December 2026",
            "location": "India",
            "required_skills": ["Solidity", "Web3", "Smart Contracts", "dApp development"],
            "description": "Premier Ethereum hackathon in India for Web3 developers and entrepreneurs.",
            "url": "https://ethindia.co/"
        },

        # Fellowships
        {
            "title": "MITACS Globalink Research Internship",
            "organization": "MITACS Canada",
            "category": "fellowships",
            "degree_level": "UG",
            "eligibility": "Full-time undergraduates from India with research interest and strong academics.",
            "benefits": "Travel, stipend CAD 6,000, research experience, and international collaboration.",
            "deadline": "22 September 2026",
            "location": "Canada",
            "required_skills": ["Research aptitude", "Academic excellence", "Recommendation letters"],
            "description": "Paid international research internship for undergraduate students at Canadian universities.",
            "url": "https://www.mitacs.ca/en/programs/globalink/globalink-research-internship"
        },
        {
            "title": "Young India Fellowship",
            "organization": "Ashoka University",
            "category": "fellowships",
            "degree_level": "UG / PG",
            "eligibility": "Graduates from any discipline with strong communication and leadership potential.",
            "benefits": "Full-tuition fellowship, liberal arts education, and lifelong alumni network.",
            "deadline": "30 November 2026",
            "location": "India",
            "required_skills": ["Critical thinking", "Writing", "Leadership", "Interdisciplinary learning"],
            "description": "One-year multidisciplinary postgraduate diploma in liberal studies at Ashoka University.",
            "url": "https://www.ashoka.edu.in/yif/"
        },
        {
            "title": "Teach For India Fellowship",
            "organization": "Teach For India",
            "category": "fellowships",
            "degree_level": "UG / PG",
            "eligibility": "Graduates committed to teaching and educational equity for two years in underserved schools.",
            "benefits": "Monthly stipend, leadership training, master's credit pathway, and alumni network.",
            "deadline": "Rolling admissions",
            "location": "India",
            "required_skills": ["Teaching", "Empathy", "Leadership", "Communication"],
            "description": "Fellowship placing graduates as full-time teachers in low-income schools across India.",
            "url": "https://www.teachforindia.org/"
        },

        # Certifications
        {
            "title": "Python for Everybody Specialization",
            "organization": "University of Michigan / Coursera",
            "category": "certifications",
            "degree_level": "Any",
            "eligibility": "Beginners with no prior programming experience.",
            "benefits": "Certificate, Python fundamentals, data structures, web scraping, and database basics.",
            "deadline": "Self-paced",
            "location": "Online",
            "required_skills": ["Basic computer skills", "Self-discipline"],
            "description": "Comprehensive beginner specialization covering Python programming and data handling.",
            "url": "https://www.coursera.org/specializations/python"
        },
        {
            "title": "AWS Certified Cloud Practitioner",
            "organization": "Amazon Web Services",
            "category": "certifications",
            "degree_level": "Any",
            "eligibility": "Anyone interested in cloud computing fundamentals; no AWS experience required.",
            "benefits": "Industry-recognized cloud certification, resume boost, and foundational AWS knowledge.",
            "deadline": "On-demand exam",
            "location": "Online / Test Center",
            "required_skills": ["Cloud concepts", "Basic IT literacy"],
            "description": "Entry-level certification validating overall cloud fluency and AWS fundamentals.",
            "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/"
        },
        {
            "title": "TensorFlow Developer Certificate",
            "organization": "Google / DeepLearning.AI",
            "category": "certifications",
            "degree_level": "UG / PG",
            "eligibility": "Developers with Python and machine learning basics ready to build models with TensorFlow.",
            "benefits": "Professional certificate demonstrating practical ML model-building skills.",
            "deadline": "On-demand exam",
            "location": "Online",
            "required_skills": ["Python", "Machine Learning", "TensorFlow", "Deep Learning"],
            "description": "Hands-on certification for building NLP, computer vision, and time-series models with TensorFlow.",
            "url": "https://www.tensorflow.org/certificate"
        },
        {
            "title": "Data Engineering with Google Cloud Professional Certificate",
            "organization": "Google Cloud / Coursera",
            "category": "certifications",
            "degree_level": "UG / PG",
            "eligibility": "Data analysts and engineers aiming to learn BigQuery, Dataflow, and Pub/Sub on GCP.",
            "benefits": "Job-ready data engineering skills, certificate, and preparation for Professional Data Engineer exam.",
            "deadline": "Self-paced",
            "location": "Online",
            "required_skills": ["SQL", "Python", "Data pipelines", "Cloud basics"],
            "description": "Specialization covering designing and building data processing systems on Google Cloud.",
            "url": "https://www.coursera.org/professional-certificates/gcp-data-engineering"
        }
    ]


class ScraperService:
    """Service to register and run multiple scrapers."""

    def __init__(self):
        self.scrapers: List[BaseOpportunityScraper] = []
        self.register(BuiltinSampleScraper())
        # Register live web scrapers
        for category, sources in SCRAPE_SOURCES.items():
            for name, url in sources:
                self.register(TrafilaturaScraper(name, url, category))

    def register(self, scraper: BaseOpportunityScraper):
        self.scrapers.append(scraper)

    def register_url(self, name: str, url: str, category: str):
        """Register a generic HTML scraper for a public website."""
        self.scrapers.append(GenericHTMLScraper(name, url, category))

    def run_all(self, output_dir: str = 'scraped_data') -> Dict[str, Any]:
        """Run all registered scrapers and save cleaned output."""
        os.makedirs(output_dir, exist_ok=True)
        all_opportunities = []
        report = []

        for scraper in self.scrapers:
            try:
                opportunities = scraper.scrape()
                all_opportunities.extend(opportunities)
                report.append({
                    'source': scraper.name,
                    'category': scraper.category,
                    'url': scraper.base_url,
                    'count': len(opportunities),
                    'status': 'success'
                })
                time.sleep(0.5)
            except Exception as exc:
                report.append({
                    'source': scraper.name,
                    'category': scraper.category,
                    'url': scraper.base_url,
                    'count': 0,
                    'status': 'error',
                    'error': str(exc)
                })

        deduplicated = preprocessing_service.remove_duplicates(all_opportunities)

        output_path = os.path.join(output_dir, 'opportunities.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'opportunities': deduplicated, 'report': report}, f, indent=2, ensure_ascii=False)

        return {
            'success': True,
            'total': len(deduplicated),
            'report': report,
            'output_path': output_path
        }


scraper_service = ScraperService()
