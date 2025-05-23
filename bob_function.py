import logging
import httpx

from pydantic import Field
from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class BobFunctionConfig(FunctionBaseConfig, name="bob"):
    """
    AIQ Toolkit function template for fetching news headlines.
    """
    news_api_key: str = Field(default="8158051f3d824aee9dfc73116e7179a2", description="API key for the News API")
    country: str = Field(default="us", description="Country code for news headlines")


@register_function(config_type=BobFunctionConfig)
async def bob(config: BobFunctionConfig, builder: Builder):
    """
    Fetches top news headlines based on the input message.
    """

    async def _response_fn(input_message: str) -> str:
        """
        Processes the input message and fetches news headlines if requested.
        """
        if not input_message.strip():
            return "Please provide a valid input."

        if input_message.lower() == "news":
            base_url = "https://newsapi.org/v2/top-headlines"
            params = {
                "country": config.country,
                "apiKey": config.news_api_key
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(base_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                # Extract headlines
                headlines = [article["title"] for article in data.get("articles", [])[:30]]
                return f"Top headlines:\n" + "\n".join(headlines)

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e}")
                return "Failed to fetch news due to an API error."
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return "An unexpected error occurred while fetching news."

        return "Input not recognized. Try typing 'news' to fetch top headlines."

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up bob workflow.")