import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chains.chat_chain import create_chat_agent, get_response
from tools.charting import render_chart
from tools.customer import (
    get_customer_info,
    get_question_limit,
    get_warning_threshold,
    is_active_customer,
)


def main():
    # Page configuration
    st.set_page_config(
        page_title="Insights Engine",
        page_icon="📊",
        layout="wide",
    )

    # Custom theme styling
    st.markdown("""
        <style>
        /* Primary color styling */
        .stButton>button {
            background-color: #9a66ee;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stButton>button:hover {
            background-color: #7b4fc0;
        }
        /* Chat message styling */
        .stChatMessage {
            border-radius: 10px;
            padding: 10px;
        }
        /* Header styling */
        .main-header {
            color: #9a66ee;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .sub-header {
            color: #666;
            font-size: 1.9rem;
            margin-bottom: 30px;
        }
        /* Pro badge styling */
        .pro-badge {
            background-color: #FFD700;
            color: #333;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            display: inline-block;
            margin: 5px;
        }
        /* Tier badge styling */
        .tier-badge {
            background-color: #e0e0e0;
            color: #333;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            display: inline-block;
        }
        /* Welcome container */
        .welcome-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
        }
        .welcome-title {
            color: #9a66ee;
            font-size: 4rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .welcome-subtitle {
            color: #666;
            font-size: 2.1rem;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "llm" not in st.session_state:
        st.session_state.llm = None
        st.session_state.tools = None

    # --- CUSTOMER AUTHENTICATION ---
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "customer_info" not in st.session_state:
        st.session_state.customer_info = None
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

    # Show welcome screen if not authenticated
    if not st.session_state.authenticated:
        show_welcome_screen()
        return

    # Check if customer is still active
    if not is_active_customer(st.session_state.customer_info):
        st.error("Your account is not active. Please contact support.")
        return
    

    # Get tier info
    tier = st.session_state.customer_info["tier"]
    question_limit = get_question_limit(tier)
    warning_threshold = get_warning_threshold(tier)

    # Check if question limit exceeded
    limit_exceeded = st.session_state.question_count >= question_limit

    # Sidebar
    with st.sidebar:
        st.image("img/logo-Ds8JU9Fb.svg", width=200)
        st.title("Insights Engine")
        st.markdown("---")

        # Display customer info and tier badge

        if tier == "pro":
            st.markdown(f'### 👤 {st.session_state.customer_info['user_id']}<span class="pro-badge">🏅 Pro</span>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'### 👤 {st.session_state.customer_info['user_id']} <span class="tier-badge">{tier.capitalize()}</span>',
                unsafe_allow_html=True,
            )

        # Question counter
        st.markdown("### Question Usage")
        st.progress(
            st.session_state.question_count / question_limit,
            text=f"{st.session_state.question_count} / {question_limit} questions used",
        )

        st.markdown("---")
        st.markdown("### What I Can Help With")
        st.markdown(
            "- Suburb and state demographics\n"
            "- Prosperity scores\n"
            "- Diversity indices\n"
            "- Migration footprints\n"
            "- Education levels\n"
            "- Social housing data\n"
            "- Home ownership rates\n"
            "- Rental affordability\n"
            "- Community stability metrics"
        )
        st.markdown("---")
        st.markdown("### Example Questions")
        st.markdown(
            "- *Top 3 most diverse suburbs in Victoria*\n"
            "- *Average prosperity score in New South Wales*\n"
            "- *Suburbs with high young family presence*\n"
            "- *Compare home ownership by state*"
        )

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.customer_info = None
            st.session_state.messages = []
            st.session_state.llm = None
            st.session_state.tools = None
            st.session_state.question_count = 0
            st.rerun()

    # Main content
    st.markdown("<span class='main-header'>AI-Powered Real Estate Research Analyst</span>", unsafe_allow_html=True)
    st.markdown("<span class='sub-header'>Ask me anything about Australian demographic data</span>", unsafe_allow_html=True)

    # Initialize agent on first message
    if st.session_state.llm is None:
        try:
            st.session_state.llm, st.session_state.tools = create_chat_agent()
        except Exception as e:
            st.error(f"Failed to initialize the AI assistant. Please check your configuration. Error: {str(e)}")
            return

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Re-render chart if chart data is stored with this message
                chart_data = message.get("chart_data")
                if chart_data and len(chart_data) > 1:
                    with st.expander("📊 Show Chart", expanded=False):
                        render_chart(chart_data)


    # Show tier-specific warnings
    if tier == "basic" and st.session_state.question_count >= warning_threshold:
        st.warning(f"⚠️ You've used {st.session_state.question_count} of {question_limit} questions. Consider upgrading to Pro for more queries!")

    if tier == "pro" and st.session_state.question_count >= warning_threshold:
        st.info(f"ℹ️ You've used {st.session_state.question_count} of {question_limit} questions.")

    # Show free user limit message
    if tier == "free" and limit_exceeded:
        st.error(
            "🚫 You've reached your question limit for the Free tier. "
            "[Upgrade to a paid plan](#) to continue asking questions."
        )


    # Chat input - disabled if limit exceeded
    prompt = st.chat_input(
        "Your query here...",
        disabled=limit_exceeded,
    )

    if prompt:
        # Check limit again before processing
        if limit_exceeded:
            st.error(
                "🚫 You've reached your question limit for the Free tier. "
                "[Upgrade to a paid plan](#) to continue asking questions."
            )
            return

        # Increment question count
        st.session_state.question_count += 1

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        st.status("⏳ Analyzing data...")
        
        # Get AI response
        response, query_data = get_response(
            prompt,
            st.session_state.llm,
            st.session_state.tools,
            st.session_state.messages,
        )

        # Add assistant response to chat history (include chart_data so it persists across reruns)
        assistant_msg = {
            "role": "assistant",
            "content": response,
        }
        if query_data and len(query_data) > 1:
            assistant_msg["chart_data"] = query_data
        st.session_state.messages.append(assistant_msg)

        # Rerun to update sidebar counter and show warnings
        st.rerun()


def show_welcome_screen():
    """Display the welcome screen prompting the user for their User ID."""
    col1, col2, col3 = st.columns(3)

    # Leave col1 and col3 empty, place the image in col2
    with col2:
        st.image("img/logo-Ds8JU9Fb.svg", width="stretch")

    st.markdown("""
        <div class="welcome-container">
            <span class="welcome-title">Welcome to Insights Engine</span>
            <span class="welcome-subtitle">
                Your intelligent demographic data analyst powered by AI
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Please enter your User ID to continue")
        user_id = st.text_input(
            "User ID",
            placeholder="e.g. user123",
            key="user_id_input",
        )

        if st.button("🚀 Start Chatting", use_container_width=True, type="primary"):
            if not user_id.strip():
                st.error("Please enter your User ID.")
                return

            # Look up customer in BigQuery
            with st.spinner("Verifying your account..."):
                customer_info = get_customer_info(user_id.strip())

            if customer_info is None:
                st.error(f"No account found for User ID: {user_id.strip()}. Please check and try again.")
                return

            if not is_active_customer(customer_info):
                st.error("Your account is not active. Please contact support to activate your account.")
                return

            # Authenticate the user
            st.session_state.authenticated = True
            st.session_state.customer_info = customer_info
            st.session_state.question_count = 0
            st.session_state.messages = []
            st.session_state.llm = None
            st.session_state.tools = None
            st.rerun()


if __name__ == "__main__":
    main()