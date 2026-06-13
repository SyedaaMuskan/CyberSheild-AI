import os
import uuid
from typing import Dict, Any
from azure.cosmos import CosmosClient, PartitionKey

class MemoryAgent:
    """
    Persistent Memory Agent using Azure Cosmos DB.
    Stores and retrieves previous scan findings to establish 'learning'.
    """
    def __init__(self):
        self.uri = os.getenv("COSMOS_DB_URI", "")
        self.key = os.getenv("COSMOS_DB_KEY", "")
        self.database_name = "SentinelDB"
        self.container_name = "ScanHistory"
        self.container = None

        if self.uri and self.key:
            try:
                self.client = CosmosClient(self.uri, credential=self.key, retry_total=0, connection_timeout=10)
                self.database = self.client.create_database_if_not_exists(id=self.database_name)
                self.container = self.database.create_container_if_not_exists(
                    id=self.container_name, 
                    partition_key=PartitionKey(path="/id")
                )
            except Exception as e:
                print(f"[WARNING] Cosmos DB Initialization Failed: {e}")

    def search(self, code: str, ast_report: Dict[str, Any] = None) -> Dict[str, Any]:
        matched = []
        if not self.container:
            # Fallback to local heuristic if no DB
            import re
            keywords = ["eval", "exec", "pickle", "subprocess", "importlib"]
            for k in keywords:
                if re.search(rf"\b{k}\b", code or ""):
                    matched.append({"pattern": k, "severity": "HIGH", "historical_occurrences": 1, "note": "Local fallback detection."})
            return {"matched_patterns": matched}

        try:
            # Search for similar AST findings in Cosmos DB
            if ast_report and ast_report.get("findings"):
                for finding in ast_report["findings"]:
                    issue = finding.get("issue", "")
                    category = finding.get("category", "")
                    
                    query = "SELECT * FROM c WHERE c.category = @category OR c.issue = @issue"
                    parameters = [
                        {"name": "@category", "value": category},
                        {"name": "@issue", "value": issue}
                    ]
                    
                    results = list(self.container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    if results:
                        matched.append({
                            "pattern": issue,
                            "severity": finding.get("severity", "HIGH"),
                            "historical_occurrences": len(results),
                            "note": f"System memory shows this {category} issue has been detected {len(results)} times previously."
                        })

        except Exception as e:
            print(f"[WARNING] Cosmos DB Search Failed: {e}")

        # Deduplicate matched patterns
        unique_matches = {m["pattern"]: m for m in matched}.values()
        
        # Calculate dynamic patch confidence based on historical successes
        occurrences = sum(m.get("historical_occurrences", 0) for m in unique_matches)
        base_confidence = 85
        patch_confidence = min(99, base_confidence + (occurrences * 2))
        
        return {
            "matched_patterns": list(unique_matches),
            "recommended_patch_confidence": patch_confidence
        }

    def store_scan(self, code: str, ast_report: Dict[str, Any], patched_code: str = ""):
        if not self.container or not ast_report:
            return
            
        try:
            for finding in ast_report.get("findings", []):
                record = {
                    "id": str(uuid.uuid4()),
                    "vulnerability": finding.get("issue", ""),
                    "category": finding.get("category", "Unknown"),
                    "severity": finding.get("severity", "LOW"),
                    "code_snippet": code[:500], # limit size
                    "fix": patched_code[:500] if patched_code else "",
                    "successful_patch": True if patched_code and patched_code != code else False
                }
                self.container.create_item(body=record)
        except Exception as e:
            print(f"[WARNING] Cosmos DB Store Failed: {e}")
