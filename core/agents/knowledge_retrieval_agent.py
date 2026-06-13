import os
from typing import Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

class KnowledgeRetrievalAgent:
    """
    Retrieval-Augmented Generation (RAG) agent that pulls official security
    documentation and mitigation strategies from Azure AI Search.
    """
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self.key = os.getenv("AZURE_SEARCH_KEY", "")
        self.index_name = "security-knowledge-index"
        self.client = None

        if self.endpoint and self.key:
            try:
                self.client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=AzureKeyCredential(self.key),
                    retry_total=0,
                    connection_timeout=10
                )
            except Exception as e:
                print(f"[WARNING] Azure AI Search Initialization Failed: {e}")

        # Fallback Azure OpenAI LLM if search index is empty/unpopulated
        endpoint_raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if endpoint_raw.endswith("/openai/v1"):
            self.openai_endpoint = endpoint_raw[:-10]
        elif endpoint_raw.endswith("/openai/v1/"):
            self.openai_endpoint = endpoint_raw[:-11]
        else:
            self.openai_endpoint = endpoint_raw

        self.openai_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "o4-mini")
        
        self.openai_client = None
        if self.openai_endpoint and self.openai_key:
            self.openai_client = AzureOpenAI(
                azure_endpoint=self.openai_endpoint,
                api_key=self.openai_key,
                api_version="2024-12-01-preview",
                max_retries=0,
                timeout=60.0
            )

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
                
            # Try Azure AI Search first
            retrieved = False
            if self.client:
                try:
                    results = self.client.search(search_text=attack_type, top=1)
                    for result in results:
                        content = result.get('content') or result.get('description') or str(result)
                        return f"[{attack_type}] Search KB: {content}"
                except Exception:
                    pass # Fallback to LLM
            
            # Fallback to LLM
            if not retrieved and self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=self.deployment_name,
                        messages=[
                            {"role": "system", "content": "You are a highly advanced enterprise security knowledge base. Provide a concise, 1-2 sentence official security context and standard mitigation strategy for the given attack type."},
                            {"role": "user", "content": f"Attack Type: {attack_type}"}
                        ]
                    )
                    content = response.choices[0].message.content.strip()
                    return f"[{attack_type}] Enterprise KB: {content}"
                except Exception:
                    pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(paths), 5)) as executor:
            results = executor.map(process_path, paths)
            for res in results:
                if res:
                    rag_context.append(res)

        return {"rag_context": rag_context}
