import os
import uuid
import json
from typing import Dict, Any

class MemoryAgent:
    """
    Persistent Memory Agent using local JSON DB.
    Stores and retrieves previous scan findings to establish 'learning'.
    """
    def __init__(self):
        self.db_path = "memory_db.json"
        
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump([], f)

    def search(self, code: str, ast_report: Dict[str, Any] = None) -> Dict[str, Any]:
        matched = []
        try:
            with open(self.db_path, "r") as f:
                history = json.load(f)
                
            if ast_report and ast_report.get("findings"):
                for finding in ast_report["findings"]:
                    issue = finding.get("issue", "")
                    category = finding.get("category", "")
                    
                    # Find matches in history
                    results = [item for item in history if item.get("category") == category or item.get("issue") == issue]
                    
                    if results:
                        matched.append({
                            "pattern": issue,
                            "severity": finding.get("severity", "HIGH"),
                            "historical_occurrences": len(results),
                            "note": f"System memory shows this {category} issue has been detected {len(results)} times previously."
                        })
        except Exception as e:
            print(f"[WARNING] Local DB Search Failed: {e}")

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
        if not ast_report:
            return
            
        try:
            with open(self.db_path, "r") as f:
                history = json.load(f)
                
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
                history.append(record)
                
            with open(self.db_path, "w") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"[WARNING] Local DB Store Failed: {e}")
