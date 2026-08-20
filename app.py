import gradio as gr
from app.main import app as fastapi_app

# Create a minimal Gradio UI (required by HF Gradio Spaces)
with gr.Blocks() as demo:
    gr.Markdown("# Waraq AI Backend\n\nAPI is running and active.")

# Mount the Gradio UI to `/gradio` so it doesn't break our `/api/*` routes
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
