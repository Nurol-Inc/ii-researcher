import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

from ii_researcher.reasoning.config import AgentConfig
from ii_researcher.reasoning.models.trace import Trace
from ii_researcher.reasoning.tools.registry import format_tool_descriptions


class OpenAIClient:
    """OpenAI API client.
    
    Each client instance has its own configuration to ensure concurrent sessions
    don't interfere with each other.
    """

    def __init__(self, config: AgentConfig):
        """Initialize the OpenAI client.

        Args:
            config: Session-specific configuration.
        """
        self.config = config

        extra = self.config.llm.extra_headers or {}
        # When the client sends Authorization in extra_headers, use it as api_key so the
        # SDK sends a single correct Bearer token (avoids env api_key overwriting or None).
        api_key = self.config.llm.api_key
        default_headers = None
        if extra:
            auth_header = extra.get("Authorization") or extra.get("authorization")
            if auth_header:
                # SDK sets "Bearer " + api_key; pass token only (strip "Bearer " if present).
                api_key = auth_header.strip()
                if api_key.lower().startswith("bearer "):
                    api_key = api_key[7:].strip()
            # Pass non-Authorization headers only so we don't duplicate Authorization.
            default_headers = {k: v for k, v in extra.items() if k.lower() != "authorization"}
            if not default_headers:
                default_headers = None

        # Create synchronous client
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config.llm.base_url,
            default_headers=default_headers,
        )

        # Create async client
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.config.llm.base_url,
            default_headers=default_headers,
        )

    def _get_messages(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the messages for the OpenAI API."""

        available_tools = format_tool_descriptions()
        system_prompt = self.config.system_prompt.format(
            available_tools=available_tools,
            current_date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": trace.query},
            {
                "role": "assistant",
                "content": trace.to_string(instructions),
                "prefix": True,
            },
        ]
        return messages

    def generate_completion(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> Any:
        """Generate a completion using the OpenAI API."""
        messages = self._get_messages(trace, instructions)

        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=messages,
                temperature=self.config.llm.temperature,
                top_p=self.config.llm.top_p,
                presence_penalty=self.config.llm.presence_penalty,
                stop=self.config.llm.stop_sequence,
            )
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            logging.error("Error generating completion: %s", str(e))
            raise

    async def generate_completion_stream(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion using the OpenAI API."""
        messages = self._get_messages(trace, instructions)

        try:
            stream = await self.async_client.chat.completions.create(
                model=self.config.llm.model,
                messages=messages,
                temperature=self.config.llm.temperature,
                top_p=self.config.llm.top_p,
                presence_penalty=self.config.llm.presence_penalty,
                stop=self.config.llm.get_effective_stop_sequence(len(trace.turns) > 0),
                stream=True,
            )

            # Process the stream
            collected_content = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_content += content
                    yield content

        except Exception as e:
            logging.error("Error generating streaming completion: %s", str(e))
            raise
