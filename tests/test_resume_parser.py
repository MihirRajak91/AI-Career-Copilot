import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.resume_parser import ResumeParser


class TestResumeParser:
    def setup_method(self):
        """Set up test fixtures"""
        try:
            self.parser = ResumeParser()
        except OSError:
            pytest.skip("spaCy model not available")
    
    def test_parse_text_basic(self):
        """Test basic text parsing functionality"""
        sample_text = """
        John Doe
        Software Engineer
        john.doe@email.com
        +1-555-123-4567
        
        SUMMARY
        Experienced software engineer with 5 years in Python development.
        
        EXPERIENCE
        Senior Developer at Tech Corp
        2020 - Present
        - Developed web applications using Python and Django
        - Led team of 3 developers
        
        SKILLS
        Python, Django, JavaScript, React, SQL
        
        EDUCATION
        Bachelor of Computer Science
        University of Technology, 2018
        """
        
        result = self.parser.parse_text(sample_text)
        
        # Check structure
        assert 'contact_info' in result
        assert 'sections' in result
        assert 'skills' in result
        assert 'experience' in result
        assert 'education' in result
        
        # Check contact info extraction
        assert result['contact_info']['email'] == 'john.doe@email.com'
        assert '555-123-4567' in result['contact_info']['phone']
        
        # Check skills extraction
        skills = result['skills']
        assert 'Python' in skills
        assert 'Django' in skills
        assert 'JavaScript' in skills
        
    def test_clean_text(self):
        """Test text cleaning functionality"""
        messy_text = "  Too   much    whitespace!!!  \n\n  And weird chars @#$%  "
        cleaned = self.parser._clean_text(messy_text)
        
        assert "  " not in cleaned
        assert cleaned.count(' ') < messy_text.count(' ')
        
    def test_extract_contact_info(self):
        """Test contact information extraction"""
        text = """
        Contact: john.doe@company.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe
        GitHub: github.com/johndoe
        """
        
        contact = self.parser._extract_contact_info(text)
        
        assert contact['email'] == 'john.doe@company.com'
        assert '555' in contact['phone']
        assert 'linkedin.com/in/johndoe' in contact['linkedin']
        assert 'github.com/johndoe' in contact['github']
    
    def test_extract_skills(self):
        """Test skills extraction"""
        skills_text = "Python, JavaScript, React, Node.js • SQL • Docker, Kubernetes"
        skills = self.parser._extract_skills(skills_text)
        
        assert 'Python' in skills
        assert 'JavaScript' in skills
        assert 'SQL' in skills
        assert 'Docker' in skills
    
    def test_parse_text_empty(self):
        """Test parsing empty text"""
        result = self.parser.parse_text("")
        
        assert result['raw_text'] == ""
        assert result['skills'] == []
        assert result['experience'] == []
        assert result['education'] == []


if __name__ == "__main__":
    pytest.main([__file__])