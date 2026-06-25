from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, SYSTEM_PROMPT, LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2, LANGCHAIN_PROJECT
from tools.bigquery_tool import BigQueryTool

import logging

logger = logging.getLogger(__name__)

# Configure root logger if no handlers exist (first-time setup)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def _build_tool_schema():
    """Build the tool schema for Gemini's native function calling."""
    return [
        {
            "name": "bigquery_query",
            "description": (
                "Execute a read-only SQL query against the Demografy Australian demographic data. "
                "The only table available is demografy.prod_tables.a_master_view. "
                "Use this to answer questions about Australian suburbs, states, and demographic KPIs."
                "Maximum rows to return should not be more than 10"
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The SQL SELECT query to execute against BigQuery.",
                    }
                },
                "required": ["query"],
            },
        }
    ]


def create_chat_agent():
    """Create and configure the chat agent with Gemini and BigQuery tool."""
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=GEMINI_TEMPERATURE,
    )

    bigquery_tool = BigQueryTool()
    tools = {"bigquery_query": bigquery_tool}

    return llm, tools


def get_response(user_input: str, llm, tools, chat_history: list) -> tuple:
    """
    Get a response from Gemini using native tool calling.

    :param user_input: The user's current message
    :param llm: The ChatGoogleGenerativeAI instance
    :param tools: Dict of tool name -> tool instance
    :param chat_history: List of {"role": "user"/"assistant", "content": "..."} dicts
    :return: Tuple of (response_text, query_data) where query_data is a list of dicts
             from BigQuery (or None if no tool was called / no data to chart)
    """
    try:
        logger.info("=" * 60)
        logger.info(f"USER INPUT: {user_input}")

        # Build messages using proper LangChain message types
        messages = []

        # System prompt
        messages.append(SystemMessage(content=SYSTEM_PROMPT))

        # Chat history
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Current user input
        messages.append(HumanMessage(content=user_input))

        # Bind tools to the LLM
        llm_with_tools = llm.bind_tools(_build_tool_schema())

        # Track raw query data for charting
        query_data = None

        # First call to the LLM
        logger.info("Calling Gemini (first turn)...")
        response = llm_with_tools.invoke(messages)

        # If the LLM wants to call a tool, execute it
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", "")

                logger.info(f"TOOL CALL: {tool_name}")
                logger.info(f"  args: {tool_args}")

                # Execute the tool
                if tool_name in tools:
                    tool_result = tools[tool_name]._run(tool_args.get("query", ""))
                    # Capture raw data for charting
                    if hasattr(tools[tool_name], "last_result") and tools[tool_name].last_result:
                        query_data = tools[tool_name].last_result
                else:
                    tool_result = f"Unknown tool: {tool_name}"

                logger.info(f"TOOL RESULT: {tool_result[:300]}")

                # Append the AI message with tool calls and the tool result
                messages.append(response)  # AIMessage with tool_calls
                messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call_id)
                )

                # Get the final response from Gemini with the tool result
                logger.info("Calling Gemini (with tool result)...")
                response = llm_with_tools.invoke(messages)

        # Extract the text response
        final_answer = response.content if hasattr(response, "content") else str(response)

        logger.info(f"FINAL RESPONSE: {final_answer[:300]}")
        logger.info("=" * 60)

        return final_answer, query_data

    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        return (
            f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question.",
            None,
        )
