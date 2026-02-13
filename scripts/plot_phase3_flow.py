"""Generate visual diagrams for CareerOS Phase 3 flow and agent map.

Usage:
  python scripts/plot_phase3_flow.py

Outputs:
  - outputs/phase3/phase3_flow.mmd
  - outputs/phase3/phase3_flow.dot
  - outputs/phase3/phase3_agents.mmd
  - outputs/phase3/phase3_agents.dot
  - outputs/phase3/phase3_layers.mmd
  - outputs/phase3/phase3_layers.dot
  - outputs/phase3/phase3_flow.png (if graphviz `dot` exists)
  - outputs/phase3/phase3_agents.png (if graphviz `dot` exists)
  - outputs/phase3/phase3_layers.png (if graphviz `dot` exists)
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


FLOW_MERMAID = """flowchart TD
    A[P20: Contract Validation] --> B[P21: LangGraph Orchestration]
    B --> C[load_context]
    C --> D[match]
    D --> E[rank]
    E --> F[generate]
    F --> G[guardrails]
    G --> H{P22: Human Approval?}
    H -->|approve| I[P23: Persist memory/state]
    H -->|reject| J[Stop + feedback]
    I --> K[P24: Evaluation Harness]
"""

FLOW_DOT = """digraph CareerOS_Phase3 {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#f8fafc", color="#334155", fontname="Helvetica"];

  p20 [label="P20\\nContract Validation"];
  p21 [label="P21\\nLangGraph Orchestration"];
  load [label="load_context"];
  match [label="match"];
  rank [label="rank"];
  gen [label="generate"];
  guard [label="guardrails"];
  p22 [shape=diamond, label="P22\\nHuman Approval?"];
  p23 [label="P23\\nPersist memory/state"];
  stop [label="Reject path\\nStop + feedback", fillcolor="#fee2e2", color="#991b1b"];
  p24 [label="P24\\nEvaluation Harness"];

  p20 -> p21 -> load -> match -> rank -> gen -> guard -> p22;
  p22 -> p23 [label="approve"];
  p22 -> stop [label="reject"];
  p23 -> p24;
}
"""

AGENTS_MERMAID = """flowchart LR
    subgraph Built_Now[Built now]
      A1[Context Loader]
      A2[Matcher Agent]
      A3[Ranker Agent]
      A4[Generator Agent]
      A5[Guardrails Agent]
    end

    subgraph Planned_Next[Planned next]
      P1[Approval Agent (P22)]
      P2[Memory Manager (P23)]
      P3[Evaluator Agent (P24)]
    end

    A1 --> A2 --> A3 --> A4 --> A5 --> P1 --> P2 --> P3
"""


LAYERS_MERMAID = """flowchart TB
    L1[L1 User/UI]
    L2[L2 API]
    L3[L3 Orchestration]
    L4[L4 Agents]
    L5[L5 Human Approval]
    L6[L6 Execution & Tracking]
    L7[L7 Analytics]
    L8[L8 Memory & Models]
    L9[L9 Governance & Ops]

    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
    L8 -.shared context.-> L3
    L8 -.retrieval.-> L4
    L9 -.policy/guardrails.-> L2
    L9 -.compliance/audit.-> L6
"""

LAYERS_DOT = """digraph CareerOS_Layers {
  rankdir=TB;
  node [shape=box, style="rounded,filled", fillcolor="#e2e8f0", color="#334155", fontname="Helvetica"];

  l1 [label="L1 User/UI"];
  l2 [label="L2 API"];
  l3 [label="L3 Orchestration"];
  l4 [label="L4 Agents"];
  l5 [label="L5 Human Approval"];
  l6 [label="L6 Execution & Tracking"];
  l7 [label="L7 Analytics"];
  l8 [label="L8 Memory & Models", fillcolor="#ddd6fe"];
  l9 [label="L9 Governance & Ops", fillcolor="#fee2e2"];

  l1 -> l2 -> l3 -> l4 -> l5 -> l6 -> l7;
  l8 -> l3 [style=dashed, label="state/context"];
  l8 -> l4 [style=dashed, label="retrieval/models"];
  l9 -> l2 [style=dashed, label="policy"];
  l9 -> l6 [style=dashed, label="audit"];
}
"""

AGENTS_DOT = """digraph CareerOS_Agents {
  rankdir=LR;
  node [shape=box, style="rounded,filled", color="#334155", fontname="Helvetica"];

  load [label="Context Loader", fillcolor="#dcfce7"];
  match [label="Matcher Agent", fillcolor="#dcfce7"];
  rank [label="Ranker Agent", fillcolor="#dcfce7"];
  gen [label="Generator Agent", fillcolor="#dcfce7"];
  guard [label="Guardrails Agent", fillcolor="#dcfce7"];

  appr [label="Approval Agent (P22)", fillcolor="#fef3c7"];
  mem [label="Memory Manager (P23)", fillcolor="#fef3c7"];
  eval [label="Evaluator Agent (P24)", fillcolor="#fef3c7"];

  load -> match -> rank -> gen -> guard -> appr -> mem -> eval;
}
"""


def _write_and_render(dot_bin: str | None, dot_path: Path, png_path: Path) -> None:
    if dot_bin:
        subprocess.run([dot_bin, "-Tpng", str(dot_path), "-o", str(png_path)], check=True)


def main() -> None:
    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)

    flow_mmd = out_dir / "phase3_flow.mmd"
    flow_dot = out_dir / "phase3_flow.dot"
    flow_png = out_dir / "phase3_flow.png"

    agents_mmd = out_dir / "phase3_agents.mmd"
    agents_dot = out_dir / "phase3_agents.dot"
    agents_png = out_dir / "phase3_agents.png"

    layers_mmd = out_dir / "phase3_layers.mmd"
    layers_dot = out_dir / "phase3_layers.dot"
    layers_png = out_dir / "phase3_layers.png"

    flow_mmd.write_text(FLOW_MERMAID, encoding="utf-8")
    flow_dot.write_text(FLOW_DOT, encoding="utf-8")
    agents_mmd.write_text(AGENTS_MERMAID, encoding="utf-8")
    agents_dot.write_text(AGENTS_DOT, encoding="utf-8")
    layers_mmd.write_text(LAYERS_MERMAID, encoding="utf-8")
    layers_dot.write_text(LAYERS_DOT, encoding="utf-8")

    dot_bin = shutil.which("dot")
    _write_and_render(dot_bin, flow_dot, flow_png)
    _write_and_render(dot_bin, agents_dot, agents_png)
    _write_and_render(dot_bin, layers_dot, layers_png)

    print(f"Wrote: {flow_mmd}")
    print(f"Wrote: {flow_dot}")
    print(f"Wrote: {agents_mmd}")
    print(f"Wrote: {agents_dot}")
    print(f"Wrote: {layers_mmd}")
    print(f"Wrote: {layers_dot}")
    if dot_bin:
        print(f"Wrote: {flow_png}")
        print(f"Wrote: {agents_png}")
        print(f"Wrote: {layers_png}")
    else:
        print("Graphviz 'dot' was not found; PNG files were not generated.")


if __name__ == "__main__":
    main()
