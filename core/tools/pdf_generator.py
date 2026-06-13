import os
from typing import Dict, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

class RiskDashboard:
    def generate(self, risk_score: int, path="risk_chart.png"):
        fig, ax = plt.subplots(figsize=(5, 3))

        color = "green" if risk_score < 50 else "orange" if risk_score < 80 else "red"

        ax.bar(["Risk"], [risk_score], color=color)
        ax.set_ylim(0, 100)
        ax.set_title("Security Risk Score")

        plt.savefig(path, bbox_inches='tight')
        plt.close()

        return path

class AttackFlowDiagram:
    def generate(self, attack_report, path="attack_graph.png"):
        G = nx.DiGraph()
        
        paths = attack_report.get("attack_paths", [])
        if not paths:
            # Create a placeholder if no attacks
            G.add_node("Safe")
        else:
            for attack in paths:
                src = "User Input"
                dst = attack.get("attack_type", "Exploit")
                G.add_edge(src, dst)

        plt.figure(figsize=(5, 3))
        nx.draw(G, with_labels=True, node_color="lightcoral", node_size=2000, arrows=True)

        plt.savefig(path, bbox_inches='tight')
        plt.close()

        return path

class AdvancedSecurityPDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.dashboard = RiskDashboard()
        self.flow = AttackFlowDiagram()

    def export(self, filename: str, analysis: dict) -> str:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        content = []

        # Custom styles
        title_style = self.styles["Title"]
        title_style.textColor = "#1e3a8a" # Indigo-900
        
        h2_style = self.styles["Heading2"]
        h2_style.textColor = "#3730a3"
        h2_style.spaceBefore = 15
        h2_style.spaceAfter = 5
        
        normal_style = self.styles["Normal"]
        normal_style.leading = 14

        content.append(Paragraph("<b>AUTONOMOUS SECURITY INTELLIGENCE REPORT</b>", title_style))
        content.append(Spacer(1, 12))

        # Executive Summary
        content.append(Paragraph("Executive Summary", h2_style))
        verdict = analysis.get('verdict', 'UNKNOWN')
        v_color = "red" if verdict == "BLOCK" else "orange" if verdict == "WARN" else "green"
        summary = f"This system analyzed the input code and computed a security risk score of <b>{analysis.get('risk_score', 0)}/100</b> with a final verdict of <font color='{v_color}'><b>{verdict}</b></font>."
        content.append(Paragraph(summary, normal_style))
        content.append(Spacer(1, 12))

        # Dashboard & Flow Graphs (side by side or sequential)
        risk_img = self.dashboard.generate(analysis.get("risk_score", 0))
        flow_img = self.flow.generate(analysis.get("attack_report", {}))
        
        # We can just put them sequentially with nice sizing
        content.append(Image(risk_img, width=250, height=150))
        content.append(Spacer(1, 10))
        content.append(Paragraph("Attack Flow Diagram", h2_style))
        content.append(Image(flow_img, width=250, height=150))
        content.append(Spacer(1, 15))

        # Enterprise Knowledge Base (RAG)
        rag_context = analysis.get("rag_report", {}).get("rag_context", [])
        if rag_context:
            content.append(Paragraph("Enterprise Knowledge Base (RAG)", h2_style))
            for ctx in rag_context:
                # Strip emojis safely for reportlab
                clean_ctx = ctx.encode('ascii', 'ignore').decode('ascii')
                content.append(Paragraph(f"• {clean_ctx}", normal_style))
            content.append(Spacer(1, 10))

        # Historical Scans (Memory)
        memory_hits = analysis.get("memory_report", {}).get("matched_patterns", [])
        if memory_hits:
            content.append(Paragraph("Historical Scans (Cosmos DB)", h2_style))
            for hit in memory_hits:
                if isinstance(hit, dict):
                    hit_str = f"Found {hit.get('pattern')} ({hit.get('historical_occurrences', 1)} times previously)"
                else:
                    hit_str = str(hit)
                clean_hit = hit_str.encode('ascii', 'ignore').decode('ascii')
                content.append(Paragraph(f"• {clean_hit}", normal_style))
            content.append(Spacer(1, 10))

        # Detailed Reasoning
        content.append(Paragraph("Raw Engine Reasoning", h2_style))
        reasoning_text = analysis.get("reasoning", "")
        # Strip all unicode/emojis to prevent ReportLab font rendering crashes
        clean_reasoning = reasoning_text.encode('ascii', 'ignore').decode('ascii')
        reasoning_html = clean_reasoning.replace("\n", "<br/>")
        content.append(Paragraph(reasoning_html, normal_style))

        doc.build(content)
        
        # Cleanup temp images
        if os.path.exists(risk_img): os.remove(risk_img)
        if os.path.exists(flow_img): os.remove(flow_img)

        return filename

def upload_to_azure(file_path, container_client):
    with open(file_path, "rb") as data:
        container_client.upload_blob(
            name=os.path.basename(file_path),
            data=data,
            overwrite=True
        )

def save_as_github_artifact(file_path):
    os.makedirs("artifacts", exist_ok=True)
    os.rename(file_path, f"artifacts/{os.path.basename(file_path)}")
