from typing import cast
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timedelta

from links import RAND_ID_MAPPING
from models import GAME_PROMPTS, GamePrompt
from chat_service import QwenChatService

# Load environment variables
load_dotenv()

# Initialize services
chat_service = QwenChatService()


@st.fragment(run_every=0.1)
def timedelta_display():
    if st.session_state.game_started and not st.session_state.game_over:
        elapsed_time = cast(
            timedelta,
            datetime.now() - st.session_state.start_time,
        ).total_seconds()
        st.write(f"**已用时:** {elapsed_time:.3f} 秒")


@st.fragment
def sidebar(game_config: GamePrompt):
    st.header("游戏设置")

    if st.button("开始新游戏"):
        # Reset game state without clearing everything
        st.session_state.messages = [
            {"role": "assistant", "content": "我们来玩猜东西游戏吧！你准备好了吗？"}
        ]
        st.session_state.game_over = False
        st.session_state.game_started = False
        st.session_state.start_time = None
        st.session_state.attempts = 0
        st.session_state.failure_reason = None

    st.header("游戏状态")
    st.write(f"**游戏:** {game_config.name}")
    st.write(f"**尝试次数:** {st.session_state.attempts} / {game_config.max_attempts}")

    if st.session_state.game_started and not st.session_state.game_over:
        timedelta_display()

    st.header("游戏规则")
    # FIXME: This keep refreshes
    st.info(
        f"你需要通过提问来猜出我心中想的东西。你有 {game_config.max_attempts} 次机会。我会根据你的问题给出提示。当你觉得知道答案时，可以直接说出你的猜测。"
    )


def main():
    """
    主页 query params: `game` 游戏 ID，默认为 1
    """
    st.title("🎮 猜东西游戏")
    # --- Game Setup ---
    if "game_id" not in st.session_state:
        rand_id = st.query_params.get("game")
        if not rand_id or (game_id := RAND_ID_MAPPING.get(rand_id)) not in GAME_PROMPTS:
            game_id = "nimo"  # Default game
        st.session_state.game_id = game_id
        st.session_state.messages = [
            {"role": "assistant", "content": "我们来玩猜东西游戏吧！你准备好了吗？"}
        ]
        st.session_state.game_over = False
        st.session_state.game_started = False
        st.session_state.start_time = None
        st.session_state.attempts = 0
        st.session_state.failure_reason = None

    game_config = GAME_PROMPTS[st.session_state.game_id]

    # --- Chat Interface ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.game_over:
        with st.sidebar:
            sidebar(game_config)
        if st.session_state.failure_reason:
            st.error(st.session_state.failure_reason)
        else:
            st.success(
                f"🎉 恭喜你答对了！答案就是：{game_config.answer}。总用时: {st.session_state.final_time:.3f} 秒"
            )
            st.balloons()
        st.stop()

    if prompt := st.chat_input("输入你的问题或猜测..."):
        if not st.session_state.game_started:
            st.session_state.start_time = datetime.now()
            st.session_state.game_started = True

        st.session_state.attempts += 1

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # --- Game Logic ---
        # Check if the user's guess is correct
        is_correct = chat_service.check_answer(prompt, st.session_state.game_id)

        if is_correct:
            st.session_state.game_over = True
            st.session_state.final_time = (
                datetime.now() - st.session_state.start_time
            ).total_seconds()
            st.rerun()

        # Check if max attempts reached
        elif st.session_state.attempts >= game_config.max_attempts:
            st.session_state.game_over = True
            st.session_state.failure_reason = f"💔 游戏结束！你没有在 {game_config.max_attempts} 次机会内猜出答案。正确答案是：{game_config.answer}"
            st.rerun()

        # If not correct, get AI response
        else:
            with st.spinner("🤖 AI正在思考中..."):
                response = chat_service.get_response_sync(
                    prompt, st.session_state.game_id
                )

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    # Sidebar is here to refresh attempt
    with st.sidebar:
        sidebar(game_config)


if __name__ == "__main__":
    main()
