from fastmcp import FastMCP
from typing import Dict, Any

from ast_analyzer import analyze_python_ast
from attack_path_generator import AttackPathGenerator

mcp = FastMCP("CyberShield AI Tools")
attack_generator = AttackPathGenerator()

@mcp.tool()
def analyze_code_ast(code: str) -> Dict[str, Any]:
    """
    Performs static AST analysis on the provided code to find vulnerabilities.
    
    Args:
        code: The raw python source code to analyze
        
    Returns:
        A dictionary containing success status, findings array, and finding count.
    """
    return analyze_python_ast(code)

@mcp.tool()
def generate_attack_paths(ast_report: Dict[str, Any], code: str) -> Dict[str, Any]:
    """
    Generates attack paths based on the code and AST findings.
    
    Args:
        ast_report: The dictionary output from analyze_code_ast
        code: The raw source code string
        
    Returns:
        A dictionary containing the generated attack paths based on vulnerabilities.
    """
    return attack_generator.generate_paths(ast_report, code)

if __name__ == "__main__":
    mcp.run()
