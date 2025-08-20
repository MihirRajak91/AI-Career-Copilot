import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.job_parser import JobParser


class TestJobParser:
    def setup_method(self):
        """Set up test fixtures"""
        try:
            self.parser = JobParser()
        except OSError:
            pytest.skip("spaCy model not available")
    
    def test_parse_job_text_basic(self):
        """Test basic job description parsing functionality"""
        sample_job = """
        Senior Software Engineer - Python/Django
        
        Tech Corp Inc.
        Location: San Francisco, CA (Remote friendly)
        Salary: $120,000 - $150,000
        
        About Us:
        We are a fast-growing startup with 50+ employees.
        
        Job Description:
        We're looking for an experienced software engineer to join our team.
        
        Requirements:
        - Bachelor's degree in Computer Science or related field
        - 5+ years of experience with Python
        - Strong knowledge of Django framework
        - Experience with AWS and Docker
        - Must have SQL database experience
        
        Nice to Have:
        - Experience with React
        - Knowledge of Kubernetes
        - Previous startup experience would be great
        
        Responsibilities:
        - Design and develop web applications
        - Collaborate with cross-functional teams
        - Write clean, maintainable code
        """
        
        result = self.parser.parse_job_text(sample_job)
        
        # Check basic structure
        assert 'requirements' in result
        assert 'responsibilities' in result
        assert 'skills' in result
        assert 'company_info' in result
        assert 'sections' in result
        
        # Check requirements classification
        requirements = result['requirements']
        assert 'must_have' in requirements
        assert 'nice_to_have' in requirements
        
        # Check that requirements are properly classified
        must_have = requirements['must_have']
        nice_to_have = requirements['nice_to_have']
        
        assert len(must_have) > 0
        assert len(nice_to_have) > 0
        
        # Check skills extraction
        skills = result['skills']
        assert 'all' in skills
        assert 'categorized' in skills
        
        skill_list = skills['all']
        assert 'Python' in skill_list
        assert 'Django' in skill_list
        assert 'AWS' in skill_list
        assert 'Docker' in skill_list
        
        # Check company info extraction
        company_info = result['company_info']
        assert 'Senior Software Engineer' in company_info['job_title']
        assert 'San Francisco' in company_info['location'] or 'remote' in company_info['location'].lower()
        assert '$120,000' in company_info['salary_range']
        assert company_info['job_level'] == 'senior'
        
    def test_clean_text(self):
        """Test text cleaning functionality"""
        messy_text = "  Too   much    whitespace!!!  \n\n  And weird chars @#$%  "
        cleaned = self.parser._clean_text(messy_text)
        
        assert "  " not in cleaned
        assert cleaned.count(' ') < messy_text.count(' ')
        
    def test_extract_skills(self):
        """Test skill extraction"""
        skills_text = """
        Looking for someone with Python, JavaScript, React experience.
        Must know AWS, Docker, and Kubernetes.
        SQL and MongoDB knowledge required.
        """
        skills = self.parser._extract_skills(skills_text)
        
        assert 'Python' in skills['all']
        assert 'JavaScript' in skills['all']
        assert 'React' in skills['all']
        assert 'AWS' in skills['all']
        assert 'Docker' in skills['all']
        assert 'SQL' in skills['all']
        
        # Check categorization
        categorized = skills['categorized']
        assert 'Python' in categorized['programming_languages']
        assert 'React' in categorized['frameworks_libraries']
        assert 'AWS' in categorized['cloud_devops']
        assert 'SQL' in categorized['databases']
    
    def test_classify_requirements(self):
        """Test requirements classification"""
        requirements = [
            "Bachelor's degree required",
            "5+ years of Python experience",
            "Nice to have: React knowledge",
            "Preferred: AWS certification",
            "Must have strong communication skills"
        ]
        nice_to_have = ["Previous startup experience would be great"]
        
        classified = self.parser._classify_requirements(requirements, nice_to_have, "")
        
        must_have = classified['must_have']
        nice_to_have_result = classified['nice_to_have']
        
        # Check that must-have requirements are properly identified
        assert any("Bachelor's degree required" in req for req in must_have)
        assert any("Must have strong communication skills" in req for req in must_have)
        
        # Check that nice-to-have requirements are properly identified
        assert any("Nice to have: React knowledge" in req for req in nice_to_have_result)
        assert any("Preferred: AWS certification" in req for req in nice_to_have_result)
        assert any("Previous startup experience would be great" in req for req in nice_to_have_result)
    
    def test_extract_company_info(self):
        """Test company information extraction"""
        job_text = """
        Senior Data Scientist
        TechCorp Inc.
        Location: New York, NY
        Full-time, Remote
        Salary: $130k - $160k
        
        We are a medium-sized company with 200+ employees.
        """
        
        company_info = self.parser._extract_company_info(job_text)
        
        assert 'Senior Data Scientist' in (company_info['job_title'] or "")
        assert company_info['job_level'] == 'senior'
        assert company_info['employment_type'] and ('full-time' in company_info['employment_type'].lower() or 'remote' in company_info['employment_type'].lower())
        assert company_info['size'] == '200+ employees'
    
    def test_extract_sections(self):
        """Test section extraction"""
        job_text = """
        Job Title: Software Engineer
        
        About Us:
        Great company doing amazing things.
        
        Requirements:
        - Python experience
        - 3+ years coding
        
        Responsibilities:
        - Write code
        - Debug issues
        
        Benefits:
        - Health insurance
        - 401k matching
        """
        
        sections = self.parser._extract_sections(job_text)
        
        assert 'about' in sections
        assert 'requirements' in sections
        assert 'responsibilities' in sections
        assert 'benefits' in sections
        
        assert 'Great company' in sections['about']
        assert 'Python experience' in sections['requirements']
        assert 'Write code' in sections['responsibilities']
        assert 'Health insurance' in sections['benefits']
    
    def test_parse_job_text_empty(self):
        """Test parsing empty job text"""
        result = self.parser.parse_job_text("")
        
        assert result['raw_text'] == ""
        assert result['requirements']['must_have'] == []
        assert result['requirements']['nice_to_have'] == []
        assert result['responsibilities'] == []
        assert result['skills']['all'] == []


if __name__ == "__main__":
    pytest.main([__file__])