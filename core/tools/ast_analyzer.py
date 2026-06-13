import ast
from typing import Dict, List, Any


class SecurityASTVisitor(ast.NodeVisitor):

    def __init__(self):
        self.findings = []

    def add_finding(self, severity, category, issue, line):
        self.findings.append({
            "severity": severity,
            "category": category,
            "issue": issue,
            "line": line
        })

    def visit_Call(self, node):
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            function_name = f"{node.func.value.id}.{node.func.attr}"

        if function_name:
            dangerous_calls = {
                "eval": ("CRITICAL", "Execution"),
                "exec": ("CRITICAL", "Execution"),
                "__import__": ("HIGH", "Imports"),
                "getattr": ("MEDIUM", "Reflection"),
                "setattr": ("MEDIUM", "Reflection"),
                "delattr": ("MEDIUM", "Reflection"),
                "pickle.loads": ("CRITICAL", "Deserialization"),
                "pickle.load": ("CRITICAL", "Deserialization"),
                "os.system": ("CRITICAL", "Execution"),
                "os.popen": ("CRITICAL", "Execution")
            }

            if function_name in dangerous_calls:
                severity, category = dangerous_calls[function_name]
                self.add_finding(severity, category, f"Dangerous function call detected: {function_name}", node.lineno)
            elif function_name == "open":
                is_static = False
                if node.args:
                    arg = node.args[0]
                    if type(arg).__name__ in ('Constant', 'Str'):
                        is_static = True
                
                if not is_static:
                    self.add_finding("CRITICAL", "Filesystem", "open() called with dynamic variable. Potential Path Traversal.", node.lineno)
                else:
                    self.add_finding("LOW", "Filesystem", "open() called with static string.", node.lineno)

        self.generic_visit(node)

    def visit_Import(self, node):

        risky_modules = {
            "subprocess",
            "pickle",
            "socket",
            "importlib"
        }

        for alias in node.names:

            if alias.name in risky_modules:

                self.add_finding(
                    "MEDIUM",
                    "Imports",
                    f"Risky module imported: {alias.name}",
                    node.lineno
                )

        self.generic_visit(node)

    def visit_ImportFrom(self, node):

        risky_modules = {
            "subprocess",
            "pickle",
            "socket",
            "importlib"
        }

        if node.module in risky_modules:

            self.add_finding(
                "MEDIUM",
                "Imports",
                f"Risky module imported: {node.module}",
                node.lineno
            )

        self.generic_visit(node)

def detect_patterns(code: str) -> List[Dict[str, Any]]:
    findings = []
    
    # SQL Injection
    # Only flag if there is a SELECT accompanied by string concatenation (+)
    import re
    if re.search(r'(?i)SELECT.*?["\']\s*\+', code) or re.search(r'(?i)f["\'].*?SELECT.*?\{.*?\}', code):
        findings.append({
            "severity": "CRITICAL",
            "category": "Injection",
            "issue": "Possible SQL injection via string concatenation or f-string detected in query.",
            "line": -1
        })
    elif "cursor.execute(" in code and "%" in code and code.count(",") == 0:
        # Simplistic check for unsafe string formatting in execute
        findings.append({
            "severity": "CRITICAL",
            "category": "Injection",
            "issue": "Possible SQL injection via string formatting.",
            "line": -1
        })

    # Authentication Bypass
    auth_indicators = ["password == 'admin'", "bypass_auth = True", "login(bypass=True)", "user == 'admin' or True"]
    for pattern in auth_indicators:
        if pattern in code:
            findings.append({
                "severity": "CRITICAL",
                "category": "Authentication",
                "issue": f"Possible Authentication Bypass via pattern: {pattern}",
                "line": -1
            })
            break
            
    # Hardcoded Secrets
    if re.search(r'(?i)(password|secret_key|api_key|secret)\s*=\s*["\'].+?["\']', code):
        findings.append({
            "severity": "CRITICAL",
            "category": "Secrets",
            "issue": "Hardcoded secret or credential detected.",
            "line": -1
        })

    # Cross-Site Scripting (XSS)
    if re.search(r'(?i)<[a-z0-9]+>.*?(["\']\s*\+\s*[a-zA-Z_]+|f["\'].*?\{.*?\})', code):
        findings.append({
            "severity": "CRITICAL",
            "category": "XSS",
            "issue": "Potential XSS detected: Unescaped string concatenation within HTML.",
            "line": -1
        })

    # XML External Entity (XXE)
    if re.search(r'(?i)import\s+xml\.etree\.ElementTree|from\s+xml\.etree\s+import', code):
        findings.append({
            "severity": "CRITICAL",
            "category": "XXE",
            "issue": "Unsafe XML parsing detected. Use 'defusedxml' to prevent XXE attacks.",
            "line": -1
        })

    return findings

def analyze_python_ast(code: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(code)
        visitor = SecurityASTVisitor()
        visitor.visit(tree)
        
        all_findings = visitor.findings + detect_patterns(code)

        return {
            "success": True,
            "findings": all_findings,
            "finding_count": len(all_findings)
        }

    except SyntaxError as e:
        # Even if AST parsing fails, try pattern matching
        pattern_findings = detect_patterns(code)
        return {
            "success": False,
            "error": f"Syntax Error: {str(e)}",
            "findings": pattern_findings,
            "finding_count": len(pattern_findings)
        }

# Backwards-compatible API: some modules expect `analyze_ast` name
analyze_ast = analyze_python_ast

__all__ = ["analyze_python_ast", "analyze_ast"]