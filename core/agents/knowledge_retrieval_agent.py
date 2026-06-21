import os
from typing import Dict, Any
from google import genai
from google.genai import types

class KnowledgeRetrievalAgent:
    """
    Retrieval-Augmented Generation (RAG) agent that pulls official security
    documentation and mitigation strategies.
    Uses a local knowledge base dictionary and falls back to Gemini.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.local_kb = {
            "SQL Injection": "Use parameterized queries or ORMs to separate code from data.",
            "Cross-Site Scripting (XSS)": "Always escape user input before rendering it in the browser.",
            "Path Traversal": "Validate file paths and restrict access to a specific directory using secure path resolution.",
            "Code Injection": "Avoid using eval() or exec() with untrusted user input."
        }

    def retrieve(self, attack_report: Dict[str, Any]) -> Dict[str, Any]:
        rag_context = []
        paths = attack_report.get("attack_paths", [])
        
        if not paths:
            return {"rag_context": rag_context}
            
        import concurrent.futures
        
        def process_path(path):
            attack_type = path.get("attack_type", "")
            if not attack_type:
                return None
                
            # Try Local KB Search first
            retrieved = False
            if attack_type in self.local_kb:
                content = self.local_kb[attack_type]
                return f"[{attack_type}] Search KB: {content}"
            
            # Fallback to LLM
            if not retrieved and self.client:
                try:
                    prompt = f"Attack Type: {attack_type}"
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction="You are a highly advanced enterprise security knowledge base. Provide a concise, 1-2 sentence official security context and standard mitigation strategy for the given attack type."
                        ),
                    )
                    content = response.text.strip()
                    return f"[{attack_type}] Enterprise KB (Gemini): {content}"
                except Exception:
                    pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(paths), 5)) as executor:
            results = executor.map(process_path, paths)
            for res in results:
                if res:
                    rag_context.append(res)

        return {"rag_context": rag_context}

