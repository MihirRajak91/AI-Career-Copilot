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
        nice_to_have = self._extract_requirements(sections.get('nice_to_have', ''))
        responsibilities = self._extract_responsibilities(sections.get('responsibilities', ''))
        skills = self._extract_skills(cleaned_text)
        company_info = self._extract_company_info(cleaned_text)
        
        # Classify requirements vs nice-to-have
        classified_requirements = self._classify_requirements(requirements, nice_to_have, cleaned_text)
        
        return {
            'raw_text': text,
            'cleaned_text': cleaned_text,
            'sections': sections,
            'requirements': classified_requirements,
            'responsibilities': responsibilities,
            'skills': skills,
            'company_info': company_info,
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize job description text"""
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s@.\-+(),:;]', ' ', text)
        # Remove excessive whitespace (do this after special character removal)
        text = re.sub(r'\s+', ' ', text)
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
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills from job description"""
        # Comprehensive skill patterns organized by category
        skill_categories = {
            'programming_languages': [
                r'\bPython\b', r'\bJava\b', r'\bJavaScript\b', r'\bTypeScript\b', 
                r'\bC\+\+\b', r'\bC#\b', r'\bGo\b', r'\bRust\b', r'\bRuby\b', 
                r'\bPHP\b', r'\bSwift\b', r'\bKotlin\b', r'\bScala\b', r'\bR\b',
                r'\bMatlab\b', r'\bPerl\b', r'\bShell\b', r'\bBash\b'
            ],
            'frameworks_libraries': [
                r'\bReact\b', r'\bAngular\b', r'\bVue\.?js\b', r'\bDjango\b', 
                r'\bFlask\b', r'\bSpring\b', r'\bExpress\b', r'\bLaravel\b',
                r'\bNodejs\b', r'\bNode\.js\b', r'\bBootstrap\b', r'\bjQuery\b',
                r'\bTensorFlow\b', r'\bPyTorch\b', r'\bScikit-learn\b', r'\bPandas\b',
                r'\bNumPy\b', r'\bKeras\b', r'\bOpenCV\b'
            ],
            'cloud_devops': [
                r'\bAWS\b', r'\bAzure\b', r'\bGCP\b', r'\bGoogle Cloud\b',
                r'\bDocker\b', r'\bKubernetes\b', r'\bJenkins\b', r'\bGit\b',
                r'\bLinux\b', r'\bTerraform\b', r'\bAnsible\b', r'\bCI/CD\b',
                r'\bDevOps\b', r'\bSpark\b', r'\bKafka\b', r'\bRedis\b'
            ],
            'databases': [
                r'\bSQL\b', r'\bNoSQL\b', r'\bMySQL\b', r'\bPostgreSQL\b',
                r'\bMongoDB\b', r'\bCassandra\b', r'\bElasticsearch\b',
                r'\bRedshift\b', r'\bOracle\b', r'\bSQLite\b'
            ],
            'tools_platforms': [
                r'\bJira\b', r'\bConfluence\b', r'\bSlack\b', r'\bTableau\b',
                r'\bPower BI\b', r'\bSalesforce\b', r'\bShopify\b', r'\bWordPress\b',
                r'\bFigma\b', r'\bSketch\b', r'\bPhotoshop\b'
            ],
            'soft_skills': [
                r'\bAgile\b', r'\bScrum\b', r'\bKanban\b', r'\bLeadership\b',
                r'\bTeamwork\b', r'\bCommunication\b', r'\bProblem.solving\b',
                r'\bCritical thinking\b', r'\bProject management\b'
            ]
        }
        
        extracted_skills = {}
        
        for category, patterns in skill_categories.items():
            category_skills = set()
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                category_skills.update(matches)
            extracted_skills[category] = list(category_skills)
        
        # Also return a flat list for backward compatibility
        all_skills = []
        for skills_list in extracted_skills.values():
            all_skills.extend(skills_list)
        
        return {
            'categorized': extracted_skills,
            'all': list(set(all_skills))  # Remove duplicates
        }
    
    def _classify_requirements(self, requirements: List[str], nice_to_have: List[str], full_text: str) -> Dict[str, List[str]]:
        """Classify requirements into must-have vs nice-to-have categories"""
        
        # Keywords that typically indicate must-have requirements
        must_have_indicators = [
            'required', 'must have', 'essential', 'mandatory', 'minimum',
            'bachelor', 'degree', 'years of experience', 'experience with',
            'proficient', 'strong knowledge', 'demonstrated experience'
        ]
        
        # Keywords that typically indicate nice-to-have requirements
        nice_to_have_indicators = [
            'preferred', 'nice to have', 'bonus', 'plus', 'ideal',
            'would be great', 'advantage', 'desirable', 'beneficial'
        ]
        
        classified = {
            'must_have': [],
            'nice_to_have': []
        }
        
        # Start with explicitly categorized items
        classified['nice_to_have'].extend(nice_to_have)
        
        # Classify each requirement
        for req in requirements:
            req_lower = req.lower()
            
            # Check for explicit indicators
            is_must_have = any(indicator in req_lower for indicator in must_have_indicators)
            is_nice_to_have = any(indicator in req_lower for indicator in nice_to_have_indicators)
            
            if is_nice_to_have and not is_must_have:
                classified['nice_to_have'].append(req)
            elif is_must_have or not is_nice_to_have:
                # Default to must-have if unclear
                classified['must_have'].append(req)
            else:
                classified['must_have'].append(req)
        
        # Remove duplicates while preserving order
        classified['must_have'] = list(dict.fromkeys(classified['must_have']))
        classified['nice_to_have'] = list(dict.fromkeys(classified['nice_to_have']))
        
        return classified
    
    def _extract_company_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract company information from job description"""
        company_info = {
            'name': None,
            'industry': None,
            'size': None,
            'location': None,
            'job_title': None,
            'job_level': None,
            'employment_type': None,
            'salary_range': None,
        }
        
        # Extract job title (usually in the first few lines or after "Job Title:", "Position:", etc.)
        title_patterns = [
            r'(?i)(?:job title|position|role)[\s:]+([^\n]+)',
            r'(?m)^[\s]*([A-Z][^\n]*(?:engineer|developer|manager|analyst|specialist|coordinator|scientist))',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                company_info['job_title'] = match.group(1).strip()
                break
        
        # If no title found, try first non-empty line that looks like a job title
        if not company_info['job_title']:
            lines = text.split('\n')[:10]  # Check more lines
            for line in lines:
                line = line.strip()
                if line and any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'scientist']):
                    company_info['job_title'] = line
                    break
        
        # Extract job level
        level_patterns = [
            r'\b(senior|sr\.?)\b',
            r'\b(junior|jr\.?)\b',
            r'\b(lead|principal|staff)\b',
            r'\b(entry.level|intern)\b',
            r'\b(mid.level|intermediate)\b'
        ]
        
        for pattern in level_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_info['job_level'] = match.group(1).lower()
                break
        
        # Extract employment type
        employment_patterns = [
            r'\b(full.time|part.time|contract|freelance|temporary|permanent)\b',
            r'\b(remote|hybrid|on.site|onsite)\b'
        ]
        
        employment_types = []
        for pattern in employment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            employment_types.extend(matches)
        
        if employment_types:
            company_info['employment_type'] = ', '.join(set(employment_types))
        
        # Extract company name (try multiple approaches)
        company_patterns = [
            r'(?i)(?:company|employer)[\s:]+([^\n]+)',
            r'(?i)(?:at|@)\s+([A-Z][a-zA-Z\s&.,]+(?:Inc|Corp|Ltd|LLC|Company))',
            r'(?i)^([A-Z][a-zA-Z\s&.,]+(?:Inc|Corp|Ltd|LLC|Company))',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                company_info['name'] = match.group(1).strip()
                break
        
        # Extract location patterns (more comprehensive)
        location_patterns = [
            r'(?i)(?:location|based in|office|headquarters)[\s:]*([a-zA-Z\s,.-]+(?:USA?|United States|UK|Canada|Australia))',
            r'(?i)(remote|hybrid|work from home)',
            r'(?i)([A-Z][a-z]+,\s*[A-Z]{2})',  # City, State format
            r'(?i)([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country format
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                company_info['location'] = match.group(1).strip()
                break
        
        # Extract salary range
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:-|to)\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*k?)\s*(?:-|to)\s*\$?(\d{1,3}(?:,\d{3})*k?)',
            r'(?i)salary[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:k|,000)?)\s*(?:-|to)\s*\$?(\d{1,3}(?:,\d{3})*(?:k|,000)?)',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                company_info['salary_range'] = f"${match.group(1)} - ${match.group(2)}"
                break
        
        # Extract company size indicators
        size_patterns = [
            r'(?i)(\d+\+?\s*(?:employees?|people|staff))',
            r'(?i)(startup|small|medium|large|enterprise|fortune \d+)',
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                company_info['size'] = match.group(1).strip()
                break
        
        return company_info


# Utility function for easy import
def parse_job_description(text: str) -> Dict:
    """Convenience function to parse a job description"""
    parser = JobParser()
    return parser.parse_job_text(text)