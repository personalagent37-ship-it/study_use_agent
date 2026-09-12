"""
Hand-Drawn System Design & Architecture Blueprint Generator.
Renders authentic student-drawn system architectures with handwritten labels,
pen flow arrows, and margin callouts across Web UI, DOCX, and PDF.
"""

import os
import re
import math
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import matplotlib
matplotlib.use("Agg")  # Non-GUI headless backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

class DiagramNode:
    def __init__(self, name: str, role: str = "", annotation: str = "", step: int = 1):
        self.name = name.strip()
        self.role = role.strip()
        self.annotation = annotation.strip()
        self.step = step

class SystemDesignParser:
    """Parses [SYSTEM_DESIGN: ...] tags from notes or synthesizes architecture from topic."""

    @staticmethod
    def parse_block(text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse [SYSTEM_DESIGN: ...] block if present in markdown text."""
        match = re.search(r"\[SYSTEM_DESIGN:\s*([\s\S]*?)\]", text, re.IGNORECASE)
        if not match:
            return None

        content = match.group(1).strip()
        lines = [l.strip() for l in content.split("\n") if l.strip()]

        title = "System Architecture Blueprint"
        flow_steps = []
        nodes = []
        callouts = []

        current_section = "general"
        for line in lines:
            lower = line.lower()
            if lower.startswith("title:"):
                title = line[6:].strip()
            elif lower.startswith("flow:"):
                raw_flow = line[5:].strip()
                flow_steps = [p.strip() for p in re.split(r"->|➔|-->", raw_flow) if p.strip()]
            elif lower.startswith(("nodes:", "components:", "stages:")):
                current_section = "nodes"
            elif lower.startswith(("callouts:", "tradeoffs:", "notes:", "bottlenecks:")):
                current_section = "callouts"
            elif line.startswith(("-", "*", "•")):
                item_text = line.lstrip("-*• ").strip()
                if current_section == "nodes":
                    # Format: Name | Role | Annotation
                    parts = [p.strip() for p in item_text.split("|")]
                    name = parts[0] if parts else "Component"
                    role = parts[1] if len(parts) > 1 else ""
                    anno = parts[2] if len(parts) > 2 else ""
                    nodes.append(DiagramNode(name, role, anno, step=len(nodes) + 1))
                else:
                    callouts.append(item_text)
            else:
                if current_section == "callouts":
                    callouts.append(line)

        # If no nodes parsed explicitly, derive them from flow steps
        if not nodes and flow_steps:
            for idx, step_name in enumerate(flow_steps, 1):
                nodes.append(DiagramNode(step_name, "System Stage", "", step=idx))

        return {
            "title": title,
            "flow": flow_steps,
            "nodes": nodes,
            "callouts": callouts
        }

    @staticmethod
    def fallback_architecture_for_topic(topic: str) -> Dict[str, Any]:
        """Synthesize authoritative architecture nodes for common student topics."""
        t_lower = topic.lower()
        if "rag" in t_lower or "retrieval" in t_lower:
            return {
                "title": "RAG (Retrieval-Augmented Generation) Architecture",
                "flow": ["User Query", "Embedding Model", "Vector DB (HNSW)", "Prompt Assembler", "LLM Generator", "Grounded Response"],
                "nodes": [
                    DiagramNode("1. User Query", "Input Prompt", "Raw text sanitized & tokenized", step=1),
                    DiagramNode("2. Embedding Model", "Query Vectorizer", "text-embedding-3 (1536 dims)", step=2),
                    DiagramNode("3. Vector DB", "Dense Retrieval", "HNSW Index Cosine Top-K=5", step=3),
                    DiagramNode("4. Context Augmenter", "Prompt Synthesizer", "Injects retrieved chunks into prompt", step=4),
                    DiagramNode("5. LLM Reasoner", "Inference Engine", "Generates grounded response", step=5),
                    DiagramNode("6. Verified Output", "Final Response", "Citations & sources attached", step=6)
                ],
                "callouts": [
                    "⚠️ Ingestion Pipeline: Docs -> Chunking (512 tokens, 10% overlap) -> Embedding -> Vector DB",
                    "💡 Golden Rule: Re-ranking (Cohere/BGE) before prompt assembly boosts precision by 20%+",
                    "⚡ Latency Breakdown: Vector Search (~25ms) | LLM Generation (~250ms)"
                ]
            }
        elif "cnn" in t_lower or "convolution" in t_lower:
            return {
                "title": "Convolutional Neural Network (CNN) Pipeline",
                "flow": ["Input Image", "Conv Layer + ReLU", "Max Pooling", "Dense Layers", "Softmax Output"],
                "nodes": [
                    DiagramNode("1. Input Image", "3D Tensor (H x W x C)", "RGB Matrix (e.g. 224x224x3)", step=1),
                    DiagramNode("2. Conv + ReLU", "Feature Extraction", "Kernels detect edges & textures", step=2),
                    DiagramNode("3. Max Pooling", "Downsampling", "Reduces spatial dims by 2x", step=3),
                    DiagramNode("4. Flatten & Dense", "Classification Head", "Fully connected reasoning", step=4),
                    DiagramNode("5. Softmax", "Probability Vector", "Sum of class scores = 1.0", step=5)
                ],
                "callouts": [
                    "📌 Invariance: Pooling gives translation invariance to small object shifts",
                    "⚠️ Vanishing Gradient: Solved by ReLU activation max(0, x)"
                ]
            }
        elif "kafka" in t_lower or "event" in t_lower or "stream" in t_lower:
            return {
                "title": "Distributed Event Streaming Architecture",
                "flow": ["Producers", "Kafka Broker Cluster", "Partition Topics", "Consumer Groups"],
                "nodes": [
                    DiagramNode("1. Producers", "Data Sources", "Microservices & IoT events", step=1),
                    DiagramNode("2. Kafka Cluster", "Brokers & KRaft", "Distributed append-only commit logs", step=2),
                    DiagramNode("3. Partitions", "Parallel Units", "Ordered messages with offsets", step=3),
                    DiagramNode("4. Consumer Groups", "Subscribers", "Horizontal scale reading", step=4)
                ],
                "callouts": [
                    "⚡ Guarantee: In-order delivery strictly guaranteed within a partition",
                    "💡 Backpressure: Consumers pull data at their own pace"
                ]
            }
        else:
            clean_title = topic.strip().title()
            return {
                "title": f"{clean_title} System Architecture",
                "flow": ["Input & Trigger", "Preprocessing", "Core Logic Engine", "Storage & Index", "Output"],
                "nodes": [
                    DiagramNode("1. Input Stage", "Client Request", "Payload validation & parsing", step=1),
                    DiagramNode("2. Processing", "Transformation", "Normalization & feature prep", step=2),
                    DiagramNode("3. Core Engine", "Algorithm / Model", "Main business/compute logic", step=3),
                    DiagramNode("4. Persistence", "Storage / Cache", "State retention & retrieval", step=4),
                    DiagramNode("5. Result Delivery", "Client Response", "Formatted output & telemetry", step=5)
                ],
                "callouts": [
                    f"📌 Core Mechanism: Continuous data transformation pipeline for {clean_title}",
                    "💡 Pro Tip: Decouple compute from storage for horizontal scalability"
                ]
            }

class HandDrawnDiagramGenerator:
    """Renders authentic hand-drawn architecture sketches as PNG images and SVGs."""

    PASTEL_COLORS = [
        "#FEF3C7",  # Amber / Yellow
        "#E0F2FE",  # Sky Blue
        "#D1FAE5",  # Mint Green
        "#EDE9FE",  # Soft Lavender
        "#FFEDD5",  # Soft Peach
        "#FCE7F3",  # Soft Pink
    ]

    @classmethod
    def generate_diagram_png(
        cls,
        spec: Dict[str, Any],
        output_path: Path | str
    ) -> str:
        """Render an authentic XKCD hand-drawn system design diagram to a PNG file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        nodes: List[DiagramNode] = spec.get("nodes", [])
        if not nodes:
            spec = SystemDesignParser.fallback_architecture_for_topic(spec.get("title", "System"))
            nodes = spec["nodes"]

        num_nodes = len(nodes)
        title = spec.get("title", "System Architecture Blueprint")
        callouts = spec.get("callouts", [])

        # Determine layout: 1 row if <= 4 nodes, 2 rows if > 4 nodes
        cols = 3 if num_nodes > 4 else num_nodes
        rows = math.ceil(num_nodes / cols)

        fig_width = max(10, cols * 3.6)
        fig_height = 4.2 + (rows * 2.6) + (len(callouts) * 0.45)

        with plt.xkcd(scale=0.9, length=100, randomness=1.8):
            fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=180)
            
            # Subtle warm notebook paper tint
            fig.patch.set_facecolor("#FAF9F6")
            ax.set_facecolor("#FAF9F6")

            # Title
            ax.text(
                0.5, 0.96, title,
                transform=ax.transAxes,
                fontsize=16,
                fontweight="bold",
                ha="center",
                va="top",
                color="#1E293B"
            )
            ax.text(
                0.5, 0.92, "★ HAND-DRAWN SYSTEM BLUEPRINT & DATA FLOW ★",
                transform=ax.transAxes,
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="top",
                color="#64748B"
            )

            # Node dimensions
            box_w = 0.24
            box_h = 0.16
            
            # Calculate coordinates for each node
            node_coords = []
            for idx, node in enumerate(nodes):
                r = idx // cols
                c = idx % cols
                # If row is odd, reverse column order for snake flow
                if r % 2 == 1:
                    c = (cols - 1) - c

                # Normalized x and y
                spacing_x = 0.90 / max(1, cols)
                spacing_y = 0.50 / max(1, rows)

                cx = 0.08 + (c * spacing_x) + (spacing_x / 2) - (box_w / 2)
                cy = 0.78 - (r * spacing_y) - (box_h / 2)

                node_coords.append((cx, cy, node))

            # Draw nodes
            for idx, (cx, cy, node) in enumerate(node_coords):
                color = cls.PASTEL_COLORS[idx % len(cls.PASTEL_COLORS)]

                # Drop shadow effect (hand-drawn pencil scribble underneath)
                shadow = patches.FancyBboxPatch(
                    (cx + 0.005, cy - 0.006), box_w, box_h,
                    boxstyle="round,pad=0.015,rounding_size=0.02",
                    transform=ax.transAxes,
                    facecolor="#CBD5E1",
                    edgecolor="none",
                    alpha=0.6,
                    zorder=2
                )
                ax.add_patch(shadow)

                # Main Box
                rect = patches.FancyBboxPatch(
                    (cx, cy), box_w, box_h,
                    boxstyle="round,pad=0.015,rounding_size=0.02",
                    transform=ax.transAxes,
                    facecolor=color,
                    edgecolor="#1E293B",
                    linewidth=1.8,
                    zorder=3
                )
                ax.add_patch(rect)

                # Node Title
                ax.text(
                    cx + box_w / 2, cy + box_h * 0.72,
                    node.name,
                    transform=ax.transAxes,
                    fontsize=10,
                    fontweight="bold",
                    ha="center",
                    va="center",
                    color="#0F172A",
                    zorder=4
                )

                # Node Role
                if node.role:
                    ax.text(
                        cx + box_w / 2, cy + box_h * 0.44,
                        f"[{node.role}]",
                        transform=ax.transAxes,
                        fontsize=8.5,
                        style="italic",
                        ha="center",
                        va="center",
                        color="#334155",
                        zorder=4
                    )

                # Node Annotation / Tip
                if node.annotation:
                    ax.text(
                        cx + box_w / 2, cy + box_h * 0.18,
                        f"✏️ {node.annotation}",
                        transform=ax.transAxes,
                        fontsize=7.5,
                        ha="center",
                        va="center",
                        color="#64748B",
                        zorder=4
                    )

            # Draw Connecting Flow Arrows
            for idx in range(len(node_coords) - 1):
                x1, y1, _ = node_coords[idx]
                x2, y2, _ = node_coords[idx + 1]

                # If on same row
                if abs(y1 - y2) < 0.05:
                    if x2 > x1:
                        start_x = x1 + box_w
                        end_x = x2
                    else:
                        start_x = x1
                        end_x = x2 + box_w
                    mid_y = y1 + box_h / 2
                    ax.annotate(
                        "",
                        xy=(end_x, mid_y),
                        xytext=(start_x, mid_y),
                        xycoords="axes fraction",
                        textcoords="axes fraction",
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color="#2563EB",
                            lw=2.0,
                            connectionstyle="arc3,rad=0.08"
                        ),
                        zorder=5
                    )
                else: # Between rows (downward snake transition)
                    start_x = x1 + box_w / 2
                    start_y = y1
                    end_x = x2 + box_w / 2
                    end_y = y2 + box_h
                    ax.annotate(
                        "",
                        xy=(end_x, end_y),
                        xytext=(start_x, start_y),
                        xycoords="axes fraction",
                        textcoords="axes fraction",
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color="#2563EB",
                            lw=2.0,
                            connectionstyle="arc3,rad=-0.15"
                        ),
                        zorder=5
                    )

            # Callouts Box (Bottom Sticky Note with real engineering tradeoffs)
            if callouts:
                callout_y = 0.22 if rows > 1 else 0.32
                callout_box = patches.FancyBboxPatch(
                    (0.06, 0.04), 0.88, callout_y,
                    boxstyle="round,pad=0.015,rounding_size=0.015",
                    transform=ax.transAxes,
                    facecolor="#FEF9C3",
                    edgecolor="#D97706",
                    linewidth=1.5,
                    zorder=3
                )
                ax.add_patch(callout_box)

                ax.text(
                    0.09, 0.04 + callout_y - 0.04,
                    "📌 ENGINEERING TRADEOFFS & BOTTLENECKS (FIELD NOTES):",
                    transform=ax.transAxes,
                    fontsize=9.5,
                    fontweight="bold",
                    ha="left",
                    va="top",
                    color="#92400E",
                    zorder=4
                )

                line_step = (callout_y - 0.06) / max(1, len(callouts))
                for c_idx, c_text in enumerate(callouts):
                    ax.text(
                        0.09, 0.04 + callout_y - 0.08 - (c_idx * line_step),
                        f"• {c_text}",
                        transform=ax.transAxes,
                        fontsize=8.5,
                        ha="left",
                        va="top",
                        color="#451A03",
                        zorder=4
                    )

            ax.axis("off")
            plt.tight_layout()
            plt.savefig(str(output_path), dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
            plt.close(fig)

        logger.info(f"System design blueprint rendered to PNG: {output_path}")
        return str(output_path)

    @classmethod
    def generate_diagram_svg(cls, spec: Dict[str, Any]) -> str:
        """Generate a clean, responsive hand-drawn SVG for interactive web viewing."""
        nodes: List[DiagramNode] = spec.get("nodes", [])
        if not nodes:
            spec = SystemDesignParser.fallback_architecture_for_topic(spec.get("title", "System"))
            nodes = spec["nodes"]

        num_nodes = len(nodes)
        title = spec.get("title", "System Architecture Blueprint")
        callouts = spec.get("callouts", [])

        width = 860
        node_width = 175
        node_height = 85
        gap = 35

        # Single row or 2-row layout
        if num_nodes <= 4:
            total_height = 240 + (len(callouts) * 32)
            svg_nodes = []
            start_x = (width - (num_nodes * (node_width + gap) - gap)) // 2
            y = 75
            for idx, node in enumerate(nodes):
                x = start_x + idx * (node_width + gap)
                color = cls.PASTEL_COLORS[idx % len(cls.PASTEL_COLORS)]
                svg_nodes.append((x, y, node, color))
        else:
            cols = math.ceil(num_nodes / 2)
            total_height = 360 + (len(callouts) * 32)
            svg_nodes = []
            spacing_x = (width - 80) // cols
            for idx, node in enumerate(nodes):
                row = idx // cols
                col = idx % cols
                if row == 1:
                    col = (cols - 1) - col # snake
                x = 45 + col * spacing_x
                y = 75 + (row * 125)
                color = cls.PASTEL_COLORS[idx % len(cls.PASTEL_COLORS)]
                svg_nodes.append((x, y, node, color))

        # Build SVG string
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" class="system-design-svg" style="width: 100%; height: auto; font-family: \'Caveat\', \'Comic Sans MS\', cursive, sans-serif;">',
            f'<defs>',
            f'  <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            f'    <path d="M 0 1 L 8 5 L 0 9 z" fill="#2563EB" />',
            f'  </marker>',
            f'  <filter id="sketch-shadow" x="-5%" y="-5%" width="115%" height="115%">',
            f'    <feDropShadow dx="3" dy="4" stdDeviation="2" flood-color="#94A3B8" flood-opacity="0.45" />',
            f'  </filter>',
            f'</defs>',
            f'<rect width="{width}" height="{total_height}" fill="#FAFAF9" rx="10" stroke="#E2E8F0" stroke-width="2" />',
            f'<text x="{width/2}" y="36" text-anchor="middle" font-size="20" font-weight="bold" fill="#0F172A">{title}</text>',
            f'<text x="{width/2}" y="54" text-anchor="middle" font-size="12" font-weight="bold" fill="#64748B">★ HAND-DRAWN SYSTEM BLUEPRINT &amp; DATA FLOW ★</text>'
        ]

        # Draw Node Boxes
        for idx, (x, y, node, color) in enumerate(svg_nodes):
            svg_parts.append(
                f'<g class="diagram-node-group" filter="url(#sketch-shadow)">'
                f'  <rect x="{x}" y="{y}" width="{node_width}" height="{node_height}" rx="8" fill="{color}" stroke="#1E293B" stroke-width="2" stroke-dasharray="3,1" />'
                f'  <text x="{x + node_width/2}" y="{y + 24}" text-anchor="middle" font-size="15" font-weight="bold" fill="#0F172A">{node.name}</text>'
            )
            if node.role:
                svg_parts.append(f'  <text x="{x + node_width/2}" y="{y + 44}" text-anchor="middle" font-size="12" font-style="italic" fill="#334155">[{node.role}]</text>')
            if node.annotation:
                svg_parts.append(f'  <text x="{x + node_width/2}" y="{y + 66}" text-anchor="middle" font-size="11" fill="#64748B">✏️ {node.annotation}</text>')
            svg_parts.append(f'</g>')

        # Draw Arrows between nodes
        for idx in range(len(svg_nodes) - 1):
            x1, y1, _, _ = svg_nodes[idx]
            x2, y2, _, _ = svg_nodes[idx + 1]

            if abs(y1 - y2) < 20:
                if x2 > x1:
                    ax1 = x1 + node_width + 2
                    ax2 = x2 - 4
                else:
                    ax1 = x1 - 2
                    ax2 = x2 + node_width + 4
                ay = y1 + node_height / 2
                svg_parts.append(f'<line x1="{ax1}" y1="{ay}" x2="{ax2}" y2="{ay}" stroke="#2563EB" stroke-width="2.5" stroke-dasharray="4,2" marker-end="url(#arrow)" />')
            else:
                # Vertical transition
                ax1 = x1 + node_width / 2
                ay1 = y1 + node_height + 2
                ax2 = x2 + node_width / 2
                ay2 = y2 - 4
                svg_parts.append(f'<path d="M {ax1} {ay1} C {ax1} {ay1 + 25}, {ax2} {ay2 - 25}, {ax2} {ay2}" stroke="#2563EB" stroke-width="2.5" stroke-dasharray="4,2" fill="none" marker-end="url(#arrow)" />')

        # Callouts / Sticky Note footer
        if callouts:
            sticky_y = total_height - (len(callouts) * 26) - 30
            sticky_h = (len(callouts) * 26) + 24
            svg_parts.append(
                f'<g class="diagram-callout-sticky">'
                f'  <rect x="40" y="{sticky_y}" width="{width - 80}" height="{sticky_h}" rx="6" fill="#FEF9C3" stroke="#D97706" stroke-width="1.5" />'
                f'  <text x="55" y="{sticky_y + 20}" font-size="13" font-weight="bold" fill="#92400E">📌 ENGINEERING TRADEOFFS &amp; FIELD NOTES:</text>'
            )
            for c_idx, callout in enumerate(callouts):
                clean_callout = callout.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                svg_parts.append(f'  <text x="55" y="{sticky_y + 42 + (c_idx * 22)}" font-size="12" fill="#451A03">• {clean_callout}</text>')
            svg_parts.append('</g>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)
