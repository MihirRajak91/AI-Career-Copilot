import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import fitz  # PyMuPDF
import docx2txt
from docx import Document
import spacy


class ResumeParser:
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
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict:
        """Parse resume from PDF or DOCX file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            text = self._extract_docx_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Parse the extracted text
        return self.parse_text(text)
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF using PyMuPDF"""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        return docx2txt.process(str(file_path)).strip()
    
    def parse_text(self, text: str) -> Dict:
        """Parse resume text and extract structured information"""
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract sections
        sections = self._extract_sections(cleaned_text)
        
        # Parse specific information
        contact_info = self._extract_contact_info(cleaned_text)
        skills = self._extract_skills(sections.get('skills', ''))
        experience = self._extract_experience(sections.get('experience', ''))
        education = self._extract_education(sections.get('education', ''))
        
        return {
            'raw_text': text,
            'cleaned_text': cleaned_text,
            'contact_info': contact_info,
            'sections': sections,
            'skills': skills,
            'experience': experience,
            'education': education,
            'summary': sections.get('summary', ''),
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize resume text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s@.\-+(),:;]', ' ', text)
        return text.strip()
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common resume sections"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'summary': r'(?i)(summary|profile|objective|about|overview)',
            'experience': r'(?i)(experience|employment|work|professional|career)',
            'education': r'(?i)(education|academic|qualification|degree)',
            'skills': r'(?i)(skills|competencies|technical|technologies|expertise)',
            'projects': r'(?i)(projects|portfolio|work samples)',
            'certifications': r'(?i)(certifications?|certificates?|licenses?)',
        }
        
        # Split text by common section indicators
        for section_name, pattern in section_patterns.items():
            match = re.search(f'{pattern}[:\s]*', text, re.IGNORECASE)
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
    
    def _extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information"""
        contact_info = {
            'email': None,
            'phone': None,
            'linkedin': None,
            'github': None,
            'location': None,
        }
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9-]+)'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group()
        
        # GitHub
        github_pattern = r'github\.com/([a-zA-Z0-9-]+)'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            contact_info['github'] = github_match.group()
        
        return contact_info
    
    def _extract_skills(self, skills_text: str) -> List[str]:
        """Extract skills from skills section"""
        if not skills_text:
            return []
        
        # Common skill separators
        skills = re.split(r'[,;\n•|]', skills_text)
        
        # Clean and filter skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            # Remove common prefixes/suffixes
            skill = re.sub(r'^[-•\s]*', '', skill)
            skill = re.sub(r'[.:\s]*$', '', skill)
            
            if skill and len(skill) > 1:
                cleaned_skills.append(skill)
        
        return cleaned_skills
    
    def _extract_experience(self, experience_text: str) -> List[Dict]:
        """Extract work experience entries"""
        if not experience_text:
            return []
        
        experiences = []
        # Split by common job entry patterns
        job_entries = re.split(r'\n(?=[A-Z][^,]*(?:,|\s+\d{4}))', experience_text)
        
        for entry in job_entries:
            if len(entry.strip()) > 20:  # Filter out very short entries
                exp_dict = self._parse_job_entry(entry.strip())
                if exp_dict:
                    experiences.append(exp_dict)
        
        return experiences
    
    def _parse_job_entry(self, entry: str) -> Optional[Dict]:
        """Parse individual job entry"""
        lines = entry.split('\n')
        if not lines:
            return None
        
        # Try to extract title, company, dates
        first_line = lines[0].strip()
        
        # Look for patterns like "Title at Company" or "Title, Company"
        title_company = None
        dates = None
        
        # Extract dates (years)
        date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)'
        date_match = re.search(date_pattern, entry, re.IGNORECASE)
        if date_match:
            dates = date_match.group()
        
        # Extract description (remaining lines)
        description_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and not re.match(r'^\d{4}', line):  # Skip date-only lines
                description_lines.append(line)
        
        return {
            'title': first_line,
            'company': None,  # Will need more sophisticated parsing
            'dates': dates,
            'description': '\n'.join(description_lines),
            'raw_text': entry
        }
    
    def _extract_education(self, education_text: str) -> List[Dict]:
        """Extract education entries"""
        if not education_text:
            return []
        
        education = []
        # Split by degree entries
        entries = re.split(r'\n(?=[A-Z][^,]*(?:degree|bachelor|master|phd|university|college))', education_text, flags=re.IGNORECASE)
        
        for entry in entries:
            if len(entry.strip()) > 10:
                edu_dict = self._parse_education_entry(entry.strip())
                if edu_dict:
                    education.append(edu_dict)
        
        return education
    
    def _parse_education_entry(self, entry: str) -> Optional[Dict]:
        """Parse individual education entry"""
        # Extract degree, institution, year
        degree_pattern = r'(bachelor|master|phd|doctorate|associate|diploma|certificate)'
        degree_match = re.search(degree_pattern, entry, re.IGNORECASE)
        
        year_pattern = r'\b(19|20)\d{2}\b'
        year_match = re.search(year_pattern, entry)
        
        return {
            'degree': degree_match.group() if degree_match else None,
            'institution': None,  # Will need more sophisticated parsing
            'year': year_match.group() if year_match else None,
            'raw_text': entry
        }


# Utility function for easy import
def parse_resume(file_path: Union[str, Path]) -> Dict:
    """Convenience function to parse a resume file"""
    parser = ResumeParser()
    return parser.parse_file(file_path)