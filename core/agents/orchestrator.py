from typing import Dict, Any
import concurrent.futures
import json
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import sys
import subprocess
import threading

# Core engines
from core.tools.recommendation_engine import RecommendationEngine
from core.tools.pdf_generator import AdvancedSecurityPDFExporter

from core.agents.memory_agent import MemoryAgent
from core.agents.critic_agent import CriticAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent

from core.agents.system_integrity_agent import SystemIntegrityAgent
from core.agents.code_quality_agent import CodeQualityAgent

from core.agents.advanced_auto_patch_agent import AdvancedAutoPatchAgent
from core.agents.security_education_agent import SecurityEducationAgent
from core.agents.security_pr_agent import SecurityPRAgent

def run_mcp_call(tool_name, args):
    """Synchronous wrapper to run an MCP tool call."""
    async def _call():
        server_params = StdioServerParameters(
            command="python",
            args=["core/tools/mcp_server.py"]
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=args)
                return json.loads(result.content[0].text)
    
    # Run asyncio loop in a new thread or use asyncio.run if safe
    try:
        loop = asyncio.get_running_loop()
        # If in an event loop, we can't use asyncio.run. We have to run it in a thread.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            return pool.submit(asyncio.run, _call()).result()
    except RuntimeError:
        return asyncio.run(_call())

class SecurityOrchestrator:

    def __init__(self):

        # Core engines
        self.recommender = RecommendationEngine()
        self.pdf_exporter = AdvancedSecurityPDFExporter()

        # Reasoning agents
        self.memory_agent = MemoryAgent()
        self.rag_agent = KnowledgeRetrievalAgent()
        self.critic_agent = CriticAgent()
        self.reflection_agent = ReflectionAgent()

        # Final systems
        self.system_integrity_agent = SystemIntegrityAgent()
        self.code_quality_agent = CodeQualityAgent()
        self.auto_patch_agent = AdvancedAutoPatchAgent()
        self.education_agent = SecurityEducationAgent()
        self.security_pr_agent = SecurityPRAgent()

        self.max_reflections = 2

    # -------------------------
    # MAIN PIPELINE
    # -------------------------

    def analyze(self, code: str) -> Dict[str, Any]:

        # 1. AST analysis via MCP
        try:
            ast_report = run_mcp_call("analyze_code_ast", {"code": code})
        except Exception as e:
            print(f"MCP Call Failed: {e}")
            from core.tools.ast_analyzer import analyze_ast
            ast_report = analyze_ast(code)
            
        # --- CIRCUIT BREAKER ---
        critical_findings = [f for f in ast_report.get("findings", []) if str(f.get("severity", "")).upper() == "CRITICAL"]
        if critical_findings:
            return self._build_fast_fail_response(code, ast_report, critical_findings)
        # -----------------------

        # 2. Attack paths via MCP
        try:
            attack_report = run_mcp_call("generate_attack_paths", {"ast_report": ast_report, "code": code})
        except Exception as e:
            print(f"MCP Call Failed: {e}")
            from core.tools.attack_path_generator import AttackPathGenerator
            ag = AttackPathGenerator()
            attack_report = ag.generate_paths(ast_report, code)

        # 3. Parallel Execution Round 1 (Independent Agents)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_integrity = executor.submit(self.system_integrity_agent.analyze, code)
            future_quality = executor.submit(self.code_quality_agent.analyze, code)
            future_memory = executor.submit(self.memory_agent.search, code, ast_report)
            future_rag = executor.submit(self.rag_agent.retrieve, attack_report)
            future_patch = executor.submit(self.auto_patch_agent.fix_file, code)

            integrity_report = future_integrity.result()
            quality_report = future_quality.result()
            memory_report = future_memory.result()
            rag_report = future_rag.result()
            patch_report = future_patch.result()

        patched_code = patch_report.get("patched_code", code)

        # 4. Parallel Execution Round 2 (Dependent Agents)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_critic = executor.submit(self.critic_agent.review, ast_report, attack_report, memory_report, rag_report)
            future_pr = executor.submit(self.security_pr_agent.generate_pr, code, patched_code, patch_report.get("fix_steps", []))
            future_edu = executor.submit(self.education_agent.explain, code, patched_code, patch_report.get("fix_steps", []))
            future_rec = executor.submit(self.recommender.generate_recommendations, attack_report)

            critic_report = future_critic.result()
            security_pr = future_pr.result()
            education_report = future_edu.result()
            recommendation_report = future_rec.result()

        # 6. Reflection loop
        reflection_count = 0
        reflection = self.reflection_agent.should_reflect(critic_report)

        while reflection.get("reflect", False) and reflection_count < self.max_reflections:

            reflection_count += 1

            try:
                ast_report = run_mcp_call("analyze_code_ast", {"code": code})
                attack_report = run_mcp_call("generate_attack_paths", {"ast_report": ast_report, "code": code})
            except Exception:
                pass # Use previous reports

            # Do not re-query Memory or RAG in the reflection loop as it adds huge network latency
            # We reuse the initial memory_report and rag_report

            critic_report = self.critic_agent.review(
                ast_report, attack_report, memory_report, rag_report
            )

            reflection = self.reflection_agent.should_reflect(critic_report)

        # 8. Risk score
        risk_score = self._calculate_risk_score(
            ast_report,
            attack_report,
            memory_report,
            critic_report,
            integrity_report,
            quality_report
        )

        verdict = self._get_verdict(risk_score)

        # 12. Final reasoning
        reasoning = self._build_reasoning(
            ast_report,
            attack_report,
            memory_report,
            rag_report,
            critic_report,
            integrity_report,
            quality_report,
            patch_report,
            education_report,
            security_pr,
            risk_score,
            verdict
        )

        result = {
            "success": True,

            "risk_score": risk_score,
            "verdict": verdict,
            "reasoning": reasoning,
            "detection_confidence": max(0, 100 - critic_report.get("confidence_penalty", 0)),
            "patch_confidence": memory_report.get("recommended_patch_confidence", 85),

            "ast_report": ast_report,
            "attack_report": attack_report,
            "memory_report": memory_report,
            "rag_report": rag_report,
            "critic_report": critic_report,
            "integrity_report": integrity_report,
            "quality_report": quality_report,

            "patch_report": patch_report,
            "security_pr": security_pr,
            "education_report": education_report,

            "reflection_passes": reflection_count
        }

        # Generate PDF report
        pdf_path = self.pdf_exporter.export("security_report.pdf", result)
        result["pdf_report"] = pdf_path

        # 13. Persistent Learning
        # Store the vulnerability and the successful patch in Cosmos DB
        self.memory_agent.store_scan(code, ast_report, patched_code)

        return result

    # -----------------------------
    # RISK ENGINE
    # -----------------------------

    def _calculate_risk_score(
        self,
        ast_report: Dict[str, Any],
        attack_report: Dict[str, Any],
        memory_report: Dict[str, Any],
        critic_report: Dict[str, Any],
        integrity_report: Dict[str, Any],
        quality_report: Dict[str, Any]
    ) -> int:

        score = 0

        severity_weights = {
            "CRITICAL": 40,
            "HIGH": 25,
            "MEDIUM": 10,
            "LOW": 5,
            "INFO": 1
        }

        for f in ast_report.get("findings", []):
            severity = f.get("severity", "LOW").upper()
            score += severity_weights.get(severity, 5)

        attack_paths = attack_report.get("attack_paths", [])
        score += len(attack_paths) * 20

        critical_paths = sum(
            1 for p in attack_paths if p.get("severity") == "CRITICAL"
        )
        score += critical_paths * 30

        memory_matches = len(memory_report.get("matched_patterns", []))
        score += memory_matches * 10

        integrity_penalty = 100 - integrity_report.get("completeness_score", 100)
        quality_penalty = 100 - quality_report.get("quality_score", 100)

        score += integrity_penalty * 0.4
        score += quality_penalty * 0.3

        score += critic_report.get("confidence_penalty", 0)
        
        # If there are any critical findings but the score is mathematically low, force it high
        if critical_paths > 0 and score < 80:
            score = 85

        return min(int(score), 100)

    # -----------------------------
    # VERDICT ENGINE
    # -----------------------------

    def _get_verdict(self, score: int) -> str:
        if score >= 75:
            return "BLOCK"
        elif score >= 40:
            return "WARN"
        return "SAFE"

    # -----------------------------
    # CIRCUIT BREAKER ENGINE
    # -----------------------------

    def _build_fast_fail_response(self, code: str, ast_report: Dict[str, Any], critical_findings: list) -> Dict[str, Any]:
        try:
            from core.tools.attack_path_generator import AttackPathGenerator
            ag = AttackPathGenerator()
            fallback_paths = ag._fallback_generate_paths(critical_findings)
        except Exception:
            fallback_paths = []
            
        attack_report = {"attack_paths": fallback_paths, "path_count": len(fallback_paths)}
        
        patch_report = self.auto_patch_agent.fix_file(code, deterministic_only=False)
        patched_code = patch_report.get("patched_code", code)
        
        memory_report = {"matched_patterns": []}
        rag_report = {"rag_context": ["Enterprise KB: This code was blocked by the deterministic circuit breaker."]}
        critic_report = {"confidence_penalty": 0}
        integrity_report = {"completeness_score": 100}
        quality_report = {"quality_score": 100}
        security_pr = {"summary": "Circuit Breaker Auto-Patch Applied."}
        education_report = {"explanations": ["Hardcoded secrets and critical flaws should be removed immediately. The code was automatically refactored securely."]}
        
        risk_score = 100
        verdict = "BLOCK"
        
        reasoning = self._build_reasoning(
            ast_report, attack_report, memory_report, rag_report,
            critic_report, integrity_report, quality_report,
            patch_report, education_report, security_pr, risk_score, verdict
        )
        
        reasoning = "⚡ FAST-FAIL CIRCUIT BREAKER ACTIVATED\n=======================================================\n" + reasoning
        
        result = {
            "success": True,
            "risk_score": risk_score,
            "verdict": verdict,
            "reasoning": reasoning,
            "detection_confidence": 100,
            "patch_confidence": 85,
            
            "patched_code": patched_code,
            
            "ast_report": ast_report,
            "attack_report": attack_report,
            "memory_report": memory_report,
            "rag_report": rag_report,
            "critic_report": critic_report,
            "integrity_report": integrity_report,
            "quality_report": quality_report,
            
            "patch_report": patch_report,
            "security_pr": security_pr,
            "education_report": education_report,
            
            "reflection_passes": 0,
            "pdf_report": ""
        }
        
        try:
            pdf_path = self.pdf_exporter.export("security_report.pdf", result)
            result["pdf_report"] = pdf_path
        except Exception:
            pass
            
        return result

    # -----------------------------
    # EXPLANATION ENGINE
    # -----------------------------

    def _build_reasoning(
        self,
        ast_report,
        attack_report,
        memory_report,
        rag_report,
        critic_report,
        integrity_report,
        quality_report,
        patch_report,
        education_report,
        security_pr,
        score,
        verdict
    ) -> str:

        lines = []

        lines.append("🧠 AUTONOMOUS SECURITY REASONING ENGINE")
        lines.append("=" * 55)

        # AST
        findings = ast_report.get("findings", [])
        lines.append(f"\n📌 Static Analysis Findings: {len(findings)}")

        for f in findings:
            lines.append(f"• [{f.get('severity')}] {f.get('issue')} (line {f.get('line', -1)})")

        # Attack paths
        attacks = attack_report.get("attack_paths", [])
        lines.append(f"\n🧨 Attack Vectors Identified: {len(attacks)}")

        for a in attacks:
            lines.append(f"• {a.get('attack_type')}: {a.get('description')}")

        # Memory
        memory_hits = memory_report.get("matched_patterns", [])
        lines.append(f"\n🧠 Memory Matches: {len(memory_hits)}")
        for hit in memory_hits:
            if isinstance(hit, dict):
                lines.append(f"• Found {hit.get('pattern')} ({hit.get('historical_occurrences', 1)} times previously)")
            else:
                lines.append(f"• {hit}")

        # RAG Context
        rag_context = rag_report.get("rag_context", [])
        if rag_context:
            lines.append(f"\n📖 Enterprise Knowledge Base:")
            for ctx in rag_context:
                lines.append(f"• {ctx}")

        # Critic
        lines.append("\n⚖️ Critic Evaluation:")
        lines.append(f"• Confidence Penalty: {critic_report.get('confidence_penalty', 0)}")

        # Patch steps
        lines.append("\n🛠️ Auto Patch Steps:")
        for step in patch_report.get("fix_steps", []):
            lines.append(f"• {step}")

        # Security PR
        lines.append("\n📦 Security PR Summary:")
        lines.append(security_pr.get("summary", "No summary available"))

        # Education
        lines.append("\n📚 Why This Fix Is Safer:")
        for e in education_report.get("explanations", []):
            lines.append(f"• {e}")

        # Risk summary
        lines.append("\n📊 Risk Summary:")
        lines.append(f"• Final Risk Score: {score}/100")
        lines.append(f"• Verdict: {verdict}")

        # Decision
        lines.append("\n🚨 Decision:")
        if verdict == "BLOCK":
            lines.append("❌ Blocked: High-confidence exploit paths detected.")
        elif verdict == "WARN":
            lines.append("⚠️ Warning: Manual review required before deployment.")
        else:
            lines.append("✅ Safe: No significant security risks detected.")

        return "\n".join(lines)