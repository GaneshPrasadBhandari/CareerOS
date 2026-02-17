import pymupdf
import httpx
import json
from loguru import logger
from src.models.schemas import ResumeSchema

class ParserAgent:
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.ollama_url = "http://127.0.0.1:11434/api/generate"

    def _extract_raw_text(self, pdf_path: str) -> str:
        doc = pymupdf.open(pdf_path)
        return "".join([page.get_text() for page in doc])

    def parse_resume(self, pdf_path: str) -> ResumeSchema:
        raw_text = self._extract_raw_text(pdf_path)
        
        # Hybrid Check: Look for Education keywords manually
        edu_keywords = ["education", "university", "college", "degree", "academic"]
        has_edu = any(key in raw_text.lower() for key in edu_keywords)
        
        if not has_edu:
            logger.warning("Fuzzy Scan: Education section might be missing or poorly formatted.")

        prompt = f"""
        Extract the resume details into a structured JSON format matching this schema:
        {ResumeSchema.model_json_schema()}
        
        Rules:
        1. Only return valid JSON.
        2. If a section is missing, return an empty list.
        
        Resume Text:
        {raw_text[:4000]}
        """

        try:
            response = httpx.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=90.0)
            
            # Clean and validate JSON
            response_data = response.json().get("response", "{}")
            return ResumeSchema.model_validate_json(response_data)
            
        except Exception as e:
            logger.error(f"AI Parsing failed: {e}")
            raise