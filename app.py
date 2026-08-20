import gradio as gr
import spaces
from app.main import app as fastapi_app

@spaces.GPU
def dummy_gpu_wakeup():
    return "Backend is running!"

# Create a minimal Gradio UI (required by HF Gradio Spaces)
with gr.Blocks() as demo:
    gr.Markdown("# Waraq AI Backend\n\nAPI is running and active.")
    btn = gr.Button("Check Status")
    out = gr.Textbox(label="System")
    btn.click(fn=dummy_gpu_wakeup, inputs=[], outputs=[out])

# Mount the Gradio UI to `/gradio` so it doesn't break our `/api/*` routes
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
