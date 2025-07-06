import redis.asyncio as redis
from llama_index.core.workflow import Context
from src.utils.func_tool_with_ctx import FunctionToolWithContext

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def fetch_customer_chat_history(ctx: Context, session_id: str) -> str:
    history = await redis_client.get(session_id)
    return history if history else f"No chat history found for session: {session_id}"

async def faq_lookup_tool(ctx: Context, question: str) -> str:
    # Mocked lookup logic
    faq_dict = {
        "reset password": "Go to settings > Account > Reset Password",
        "cancel subscription": "Visit the subscription page and click 'Cancel Subscription'"
    }
    for key, ans in faq_dict.items():
        if key in question.lower():
            return ans
    return "I'm escalating this to an agent for more accurate support."

async def ticket_status_checker(ctx: Context, ticket_id: str) -> str:
    return f"Ticket {ticket_id} is currently being reviewed by our support team."

async def suggest_next_step(ctx: Context, issue_description: str) -> str:
    if "login" in issue_description.lower():
        return "Try resetting your password or clearing your browser cookies."
    if "billing" in issue_description.lower():
        return "Please review your billing page for pending invoices."
    return "Would you like me to connect you with a support agent?"

async def get_product_doc_snippet(ctx: Context, error_code: str) -> str:
    docs = {
        "ERR_401": "Unauthorized access. Check if your token is valid.",
        "ERR_500": "Internal server error. Try again later or contact support."
    }
    return docs.get(error_code, "No documentation available for this error code.")

async def raise_ticket_on_behalf(ctx: Context, user_email: str, issue: str) -> str:
    return f"A support ticket has been drafted for {user_email} with the issue: '{issue}'. Please review and approve."

async def compose_response_for_complex_issue(ctx: Context, issue_summary: str) -> str:
    return f"Drafted response: 'We understand your issue: {issue_summary}. Our technical team is actively working on it. We will get back shortly.' Please approve before sending."


tools = [
    FunctionToolWithContext.from_defaults(async_fn=fetch_customer_chat_history),
    FunctionToolWithContext.from_defaults(async_fn=faq_lookup_tool),
    FunctionToolWithContext.from_defaults(async_fn=ticket_status_checker),
    FunctionToolWithContext.from_defaults(async_fn=suggest_next_step),
    FunctionToolWithContext.from_defaults(async_fn=get_product_doc_snippet),
    FunctionToolWithContext.from_defaults(async_fn=raise_ticket_on_behalf),
    FunctionToolWithContext.from_defaults(async_fn=compose_response_for_complex_issue),
]

tools_needing_approval = [
    FunctionToolWithContext.from_defaults(async_fn=get_product_doc_snippet),
    FunctionToolWithContext.from_defaults(async_fn=raise_ticket_on_behalf),
    FunctionToolWithContext.from_defaults(async_fn=compose_response_for_complex_issue),
]
