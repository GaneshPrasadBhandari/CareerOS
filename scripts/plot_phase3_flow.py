"""Generate a visual diagram for CareerOS Phase 3 (P20-P24) flow.

Usage:
  python scripts/plot_phase3_flow.py

Outputs:
  - outputs/phase3/phase3_flow.mmd (Mermaid source)
  - outputs/phase3/phase3_flow.dot (Graphviz DOT source)
  - outputs/phase3/phase3_flow.png (if graphviz `dot` is available)
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


MERMAID = """flowchart TD
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

DOT = """digraph CareerOS_Phase3 {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#f8fafc", color="#334155", fontname="Helvetica"];

  p20 [label="P20\nContract Validation"];
  p21 [label="P21\nLangGraph Orchestration"];
  load [label="load_context"];
  match [label="match"];
  rank [label="rank"];
  gen [label="generate"];
  guard [label="guardrails"];
  p22 [shape=diamond, label="P22\nHuman Approval?"];
  p23 [label="P23\nPersist memory/state"];
  stop [label="Reject path\nStop + feedback", fillcolor="#fee2e2", color="#991b1b"];
  p24 [label="P24\nEvaluation Harness"];

  p20 -> p21 -> load -> match -> rank -> gen -> guard -> p22;
  p22 -> p23 [label="approve"];
  p22 -> stop [label="reject"];
  p23 -> p24;
}
"""


def main() -> None:
    out_dir = Path("outputs/phase3")
    out_dir.mkdir(parents=True, exist_ok=True)

    mmd_path = out_dir / "phase3_flow.mmd"
    dot_path = out_dir / "phase3_flow.dot"
    png_path = out_dir / "phase3_flow.png"

    mmd_path.write_text(MERMAID, encoding="utf-8")
    dot_path.write_text(DOT, encoding="utf-8")

    dot_bin = shutil.which("dot")
    if dot_bin:
        subprocess.run([dot_bin, "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
        print(f"Wrote: {mmd_path}")
        print(f"Wrote: {dot_path}")
        print(f"Wrote: {png_path}")
    else:
        print("Graphviz 'dot' was not found; wrote Mermaid + DOT source files only.")
        print(f"Wrote: {mmd_path}")
        print(f"Wrote: {dot_path}")


if __name__ == "__main__":
    main()
