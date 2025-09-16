import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi.responses import RedirectResponse
import gradio as gr
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from gradio import themes

from .chat_service import QwenChatService
from .links import RAND_ID_MAPPING
from .models import GAME_PROMPTS

# Load environment variables
load_dotenv()

# Initialize services
chat_service = QwenChatService()

# --- Gradio App ---


def create_game_ui(game_id: str = "nimo"):
    """Creates the Gradio UI for the guessing game."""
    game_config = GAME_PROMPTS[game_id]

    with gr.Blocks(title="🎮 猜东西游戏", theme=themes.Soft()) as demo:
        timer = gr.Timer(0.5)
        # Game State
        state = gr.State(
            {
                "game_id": game_id,
                "messages": [gr.ChatMessage("我们来玩猜东西游戏吧！你准备好了吗？")],
                "game_over": False,
                "game_started": False,
                "start_time": None,
                "failure_reason": None,
                "final_time": None,
            }
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    type="messages",
                    value=[
                        {
                            "role": "assistant",
                            "content": "我们来玩猜东西游戏吧！你准备好了吗？",
                        }
                    ],
                    label="游戏对话",
                    bubble_full_width=False,
                    height=600,
                )
                user_input = gr.Textbox(
                    placeholder="输入你的问题或猜测...",
                    label="你的回答",
                    autofocus=True,
                )
            with gr.Column(scale=1):
                with gr.Accordion("游戏状态", open=True):
                    gr.Markdown(f"**游戏:** {game_config.name}")
                    timer_display = gr.Markdown("**已用时:** 0.000 秒")

                with gr.Accordion("游戏设置", open=True):
                    new_game_button = gr.Button("🚀 开始新游戏", variant="primary")

                game_over_display = gr.Markdown(visible=False)

        async def handle_user_input(prompt: str, current_state: dict):
            """Main game logic handler."""
            if not prompt or current_state["game_over"]:
                return (
                    current_state,
                    current_state["messages"],
                    "",
                    gr.update(visible=current_state["game_over"]),
                )

            current_state["messages"].append(gr.ChatMessage(prompt, "user"))

            if not current_state["game_started"]:
                current_state["start_time"] = datetime.now()
                current_state["game_started"] = True

            # --- Game Logic ---
            is_correct = chat_service.check_answer(prompt, current_state["game_id"])

            if is_correct:
                current_state["game_over"] = True
                current_state["final_time"] = (
                    datetime.now() - current_state["start_time"]
                ).total_seconds()
                success_message = f"🎉 恭喜你答对了！答案就是：{game_config.answer}。总用时: {current_state['final_time']:.3f} 秒"
                game_over_md = gr.Markdown(
                    f'<div style="color: green; font-weight: bold;">{success_message}</div>',
                    visible=True,
                )
                return current_state, current_state["messages"], "", game_over_md

            # If not correct, get AI response
            response = await chat_service.get_response(prompt, current_state["game_id"])
            current_state["messages"].append(gr.ChatMessage(response))

            return (
                current_state,
                current_state["messages"],
                "",
                gr.Markdown(visible=False),
            )

        async def update_displays(current_state: dict):
            """Updates the timer displays."""
            elapsed_time = 0.0
            if current_state["game_started"] and not current_state["game_over"]:
                elapsed_time = (
                    datetime.now() - current_state["start_time"]
                ).total_seconds()
            elif current_state["game_over"] and current_state["final_time"]:
                elapsed_time = current_state["final_time"]

            timer_str = f"**已用时:** {elapsed_time:.3f} 秒"
            return timer_str

        timer.tick(
            update_displays,
            inputs=[state],
            outputs=[timer_display],
        )

        def reset_game():
            """Resets the game to its initial state."""
            initial_state = {
                "game_id": game_id,
                "messages": [gr.ChatMessage("我们来玩猜东西游戏吧！你准备好了吗？")],
                "game_over": False,
                "game_started": False,
                "start_time": None,
                "failure_reason": None,
                "final_time": None,
            }
            return (
                initial_state,
                [
                    {
                        "role": "assistant",
                        "content": "我们来玩猜东西游戏吧！你准备好了吗？",
                    }
                ],
                gr.Markdown(visible=False),
                "",
            )

        # Event Listeners
        user_input.submit(
            handle_user_input,
            inputs=[user_input, state],
            outputs=[state, chatbot, user_input, game_over_display],
            show_progress="full",
        )

        new_game_button.click(
            reset_game,
            inputs=[],
            outputs=[state, chatbot, game_over_display, user_input],
        )

    return demo


def create_server():
    app = FastAPI()

    for rand_id, game_id in RAND_ID_MAPPING.items():
        game_app = create_game_ui(game_id)
        gr.mount_gradio_app(app, game_app, path=f"/{rand_id}/")

    return app


# --- FastAPI Server ---
app = create_server()


@app.get("/")
async def root():
    """Default redirect to 'nimo' game."""
    # Default to 'nimo' game
    nimo_rand_id = next(
        (k for k, v in RAND_ID_MAPPING.items() if v == "nimo"),
        list(RAND_ID_MAPPING.keys())[0] if RAND_ID_MAPPING else None,
    )

    if nimo_rand_id:
        return RedirectResponse(url=f"/{nimo_rand_id}")

    return "No games available."
