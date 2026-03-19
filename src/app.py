import gradio as gr

from src.config.settings import Settings
from src.core import Neo4jClient, NimClient
from src.qa.agent import QAAgent
from src.ui.competency_map import build_competency_graph

try:
    from src.jd_match.agent import JDMatchAgent
except ImportError:
    JDMatchAgent = None

COLORIZE_JS = """
() => {
    new MutationObserver(() => {
        document.querySelectorAll('#jd-results-table td').forEach(td => {
            const t = td.textContent.trim();
            if (t === 'Strong') { td.style.color = '#22c55e'; td.style.fontWeight = 'bold'; }
            else if (t === 'Partial') { td.style.color = '#eab308'; td.style.fontWeight = 'bold'; }
            else if (t === 'None') { td.style.color = '#ef4444'; td.style.fontWeight = 'bold'; }
        });
    }).observe(document.body, {childList: true, subtree: true});
}
"""


def create_app():
    settings = Settings.load()
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri, user=settings.neo4j_user, password=settings.neo4j_password,
    )
    nim_client = NimClient(api_key=settings.nvidia_api_key)
    qa_agent = QAAgent(neo4j_client, nim_client)
    jd_agent = JDMatchAgent(neo4j_client, nim_client) if JDMatchAgent else None

    def chat_respond(message, history):
        history = history or []
        history.append({"role": "user", "content": message})
        for chunk in qa_agent.answer_stream(message):
            yield history + [{"role": "assistant", "content": chunk}], ""

    def analyze_jd(jd_text):
        if not jd_agent:
            return 0.0, [["JDMatchAgent not available", "None", "Module not installed"]]
        report = jd_agent.match(jd_text)
        rows = [[r.requirement, r.confidence, r.evidence_summary] for r in report.results]
        return report.match_percentage, rows

    def render_graph():
        try:
            return build_competency_graph(neo4j_client)
        except Exception as e:
            return f"<p>Could not load graph: {e}</p>"

    with gr.Blocks(title="ShowMeOff") as app:
        with gr.Tab("Chat"):
            chatbot = gr.Chatbot()
            msg = gr.Textbox(placeholder="Ask about this engineer's skills...")
            msg.submit(chat_respond, [msg, chatbot], [chatbot, msg])

        with gr.Tab("JD Match"):
            jd_input = gr.Textbox(lines=10, placeholder="Paste job description here...")
            analyze_btn = gr.Button("Analyze Match")
            match_pct = gr.Number(label="Match Percentage", precision=1)
            results_table = gr.Dataframe(
                headers=["Requirement", "Confidence", "Evidence Summary"],
                datatype=["str", "str", "str"],
                elem_id="jd-results-table",
            )
            analyze_btn.click(analyze_jd, [jd_input], [match_pct, results_table])

        with gr.Tab("Skills Map"):
            graph_html = gr.HTML()
            refresh_btn = gr.Button("Refresh")
            refresh_btn.click(render_graph, [], [graph_html])
            app.load(render_graph, [], [graph_html])

    return app


if __name__ == "__main__":
    create_app().launch(server_port=7860, share=False, js=COLORIZE_JS)
