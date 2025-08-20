import re
from typing import Dict, List, Optional
import spacy


class JobParser:
    def __init__(self):
        self.nlp = None
        self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Load spaCy model for NLP processing"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model 'en_core_web_sm' not found. Please install it with:")
            print("python -m spacy download en_core_web_sm")
            raise
    
    def parse_job_text(self, text: str) -> Dict:
        """Parse job description text and extract structured information"""
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract sections
        sections = self._extract_sections(cleaned_text)
        
        # Parse specific information
        requirements = self._extract_requirements(sections.get('requirements', ''))
        responsibilities = self._extract_responsibilities(sections.get('responsibilities', ''))
        skills = self._extract_skills(cleaned_text)
        company_info = self._extract_company_info(cleaned_text)
        
        return {
            'raw_text': text,
            'cleaned_text': cleaned_text,
            'sections': sections,
            'requirements': requirements,
            'responsibilities': responsibilities,
            'skills': skills,
            'company_info': company_info,
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize job description text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s@.\-+(),:;]', ' ', text)
        return text.strip()
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common job description sections"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'requirements': r'(?i)(requirements?|qualifications?|what we.re looking for|must have)',
            'responsibilities': r'(?i)(responsibilities?|duties|what you.ll do|role|position)',
            'benefits': r'(?i)(benefits?|perks|what we offer|compensation)',
            'about': r'(?i)(about|company|who we are)',
            'nice_to_have': r'(?i)(nice to have|preferred|bonus|plus)',
        }
        
        # Split text by common section indicators
        for section_name, pattern in section_patterns.items():
            match = re.search(f'{pattern}[:\\s]*', text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                # Find next section or end of text
                next_sections = []
                for other_pattern in section_patterns.values():
                    if other_pattern != pattern:
                        next_match = re.search(other_pattern, text[start_pos:], re.IGNORECASE)
                        if next_match:
                            next_sections.append(start_pos + next_match.start())
                
                if next_sections:
                    end_pos = min(next_sections)
                    sections[section_name] = text[start_pos:end_pos].strip()
                else:
                    sections[section_name] = text[start_pos:].strip()
        
        return sections
    
    def _extract_requirements(self, requirements_text: str) -> List[str]:
        """Extract requirements from requirements section"""
        if not requirements_text:
            return []
        
        # Split by bullet points or line breaks
        requirements = re.split(r'[•\n-]', requirements_text)
        
        # Clean and filter requirements
        cleaned_requirements = []
        for req in requirements:
            req = req.strip()
            # Remove common prefixes/suffixes
            req = re.sub(r'^[-•\s]*', '', req)
            req = re.sub(r'[.:\s]*$', '', req)
            
            if req and len(req) > 5:  # Filter out very short items
                cleaned_requirements.append(req)
        
        return cleaned_requirements
    
    def _extract_responsibilities(self, responsibilities_text: str) -> List[str]:
        """Extract responsibilities from responsibilities section"""
        if not responsibilities_text:
            return []
        
        # Split by bullet points or line breaks
        responsibilities = re.split(r'[•\n-]', responsibilities_text)
        
        # Clean and filter responsibilities
        cleaned_responsibilities = []
        for resp in responsibilities:
            resp = resp.strip()
            # Remove common prefixes/suffixes
            resp = re.sub(r'^[-•\s]*', '', resp)
            resp = re.sub(r'[.:\s]*$', '', resp)
            
            if resp and len(resp) > 5:  # Filter out very short items
                cleaned_responsibilities.append(resp)
        
        return cleaned_responsibilities
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from job description"""
        # Common technical skills patterns
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Django|Flask|Spring|Express|Laravel)\b',
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|Linux|SQL|NoSQL)\b',
            r'\b(?:TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Spark|Kafka)\b',
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
        
        return list(skills)
    
    def _extract_company_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract company information from job description"""
        company_info = {
            'name': None,
            'industry': None,
            'size': None,
            'location': None,
        }
        
        # Try to extract company name (usually in the first few lines)
        lines = text.split('\n')[:5]
        for line in lines:
            if any(word in line.lower() for word in ['company', 'corp', 'inc', 'ltd']):
                company_info['name'] = line.strip()
                break
        
        # Extract location patterns
        location_pattern = r'(?i)(location|based in|remote|hybrid)[\s:]*([a-zA-Z\s,]+)'
        location_match = re.search(location_pattern, text)
        if location_match:
            company_info['location'] = location_match.group(2).strip()
        
        return company_info


# Utility function for easy import
def parse_job_description(text: str) -> Dict:
    """Convenience function to parse a job description"""
    parser = JobParser()
    return parser.parse_job_text(text)