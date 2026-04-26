from __future__ import annotations

from pathlib import Path

from app.graph import build_graph


OUTPUT_PNG = Path(__file__).resolve().parent / "agent_graph.png"
OUTPUT_MMD = Path(__file__).resolve().parent / "agent_graph.mmd"


def main() -> None:
    app = build_graph()
    graph = app.get_graph()

    try:
        png_bytes = graph.draw_mermaid_png(max_retries=5, retry_delay=2.0)
        OUTPUT_PNG.write_bytes(png_bytes)
        print(f"已生成架构图 PNG: {OUTPUT_PNG}")
        return
    except Exception as exc:
        mermaid_text = graph.draw_mermaid()
        OUTPUT_MMD.write_text(mermaid_text, encoding="utf-8")
        print("PNG 渲染失败，已导出 Mermaid 源码。")
        print(f"失败原因: {exc}")
        print(f"Mermaid 文件: {OUTPUT_MMD}")


if __name__ == "__main__":
    main()
