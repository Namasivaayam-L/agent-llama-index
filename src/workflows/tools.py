from typing import Dict, Any
from config.logging import logger

from llama_index.core.workflow import Context
from src.utils.func_tool_with_ctx import FunctionToolWithContext
from llama_index.core.tools import FunctionTool

async def license_api(
    ctx: Context,
    license_id: str
) -> str:
    """
    Use this function to retrieve the license using license_id
    Args:
        license_id: The ID of the license to retrieve or manage.
    """

    logger.info(f"Calling license API for license ID: {license_id}")

    return f"License API called with license ID: {license_id}"


async def proposal_builder_api(
    ctx: Context,
    oppty_id: str
) -> str:
    """
    Generate and manage proposal documents for opportunities.
    Args:
        oppty_id: The ID of the opportunity for which the proposal is being generated.
    """

    logger.info(f"Calling proposal builder API for opportunity ID: {oppty_id}")

    return f"Proposal builder API called with opportunity ID: {oppty_id}"


async def process_sql_query_chain(
    ctx: Context,
    question: str
) -> str:
    """
    Take a natural language question about opportunities and return relevant data.
    
    Args:
        question: A natural language question about opportunities data
    """
    user_id = await ctx.get('user_id',None)
    customer_data = await ctx.get('customer_data',None)

    logger.info(f"Processing SQL query chain with params: {question}, {user_id}, {customer_data}")

    return f"Getting data from snowflake.{question}, {user_id}, {customer_data}"


def update_oppty_field(oppty_id: str, field_name: str, field_value: str) -> str:
    """
    Update specific fields in opportunity records based on input parameters.

    Args:

        oppty_id: The ID of the opportunity to update.
        field_name: The name of the field to be updated.
        field_value: The new value to set for the specified field.

    """
    logger.info(f"Updating opportunity field: {oppty_id}, {field_name}, {field_value}")

    return f"Updating opportunity field: {oppty_id}, {field_name}, {field_value}"


tools = [
    FunctionToolWithContext.from_defaults(async_fn=process_sql_query_chain),
    FunctionTool.from_defaults(update_oppty_field),
    FunctionToolWithContext.from_defaults(async_fn=license_api),
    FunctionToolWithContext.from_defaults(async_fn=proposal_builder_api),
]


tools_needing_approval = tools[:2]      