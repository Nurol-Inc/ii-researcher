import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional, Set, Tuple, Union

from ii_researcher.reasoning.builders.report import ReportBuilder
from ii_researcher.reasoning.tools.tool_history import ToolHistory
from ii_researcher.reasoning.clients.openai_client import OpenAIClient
from ii_researcher.reasoning.config import create_config, update_config, AgentConfig
from ii_researcher.reasoning.models.action import Action
from ii_researcher.reasoning.models.output import ModelOutput
from ii_researcher.reasoning.models.trace import Trace, Turn
from ii_researcher.reasoning.tools.registry import (
    format_tool_descriptions,
    get_all_tools,
    get_tool,
)
from ii_researcher.reasoning.builders.report import ReportType

# Type alias for progress callback
ProgressCallback = Callable[[float, float, str], Awaitable[None]]


class ReasoningAgent:
    """AI agent that performs research and answers questions.
    
    This agent is designed to be session-safe for concurrent execution.
    Each agent instance maintains its own isolated state including:
    - Configuration settings
    - Tool history (visited URLs, searched queries)
    - Session-specific tool state (to prevent cross-session interference)
    
    Multiple agents can run concurrently without affecting each other's state.
    """

    def __init__(
        self,
        question: str,
        report_type: ReportType = ReportType.ADVANCED,
        stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        override_config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        llm_request_headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the agent.

        Args:
            question: The research question to answer
            report_type: Type of report to generate (BASIC or ADVANCED)
            stream_event: Optional callback for streaming events
            override_config: Optional configuration overrides
            progress_callback: Optional async callback for progress updates (progress, total, message)
            llm_request_headers: Optional headers to forward to LLM API (e.g. Authorization, X-Application-Name)
        """
        self.question = question
        self.tool_history = ToolHistory()
        self.trace = Trace(query=question, turns=[])
        self.stream_event = stream_event
        self.report_type = report_type
        self._progress_callback = progress_callback
        self._llm_request_headers = llm_request_headers if llm_request_headers else None

        # Estimated total turns for progress calculation
        self._estimated_total_turns = 10
        self._current_stage = "initializing"

        # Session-isolated state for tools
        self._session_searched_queries: Set[str] = set()
        self._session_visited_urls: Set[str] = set()

        # Create a new isolated config instance for this session
        self.config = create_config()
        if override_config:
            update_config(override_config, self.config)
        if self._llm_request_headers:
            self.config.llm.extra_headers = self._llm_request_headers

        # Create OpenAI client with session config
        self.client = OpenAIClient(config=self.config)

        # Update system prompt with available tools and current date
        available_tools = format_tool_descriptions()
        self.instructions = self.config.instructions.format(
            current_date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            available_tools=available_tools,
        )

        logging.info("ReasoningAgent initialized with question: %s", question)

    async def _report_progress(self, progress: float, total: float, message: str) -> None:
        """Report progress if a callback is registered.
        
        Args:
            progress: Current progress value (0-100)
            total: Total progress value (usually 100)
            message: Human-readable progress message
        """
        if self._progress_callback:
            try:
                await self._progress_callback(progress, total, message)
            except Exception as e:
                logging.warning(f"Progress callback failed: {e}")

    def _calculate_progress(self, turn: int, stage: str, substage: float = 0.0) -> float:
        """Calculate progress percentage based on current turn and stage.
        
        Progress breakdown:
        - Initializing: 0-5%
        - Reasoning turns: 5-70% (distributed across estimated turns)
          - Each turn has substages: thinking (0.0), tool_start (0.3), tool_exec (0.5), tool_done (0.8)
        - Report generation: 70-95%
          - Substages: start (0.0), analyzing (0.3), writing (0.6), formatting (0.9)
        - Complete: 100%
        
        Args:
            turn: Current turn number
            stage: Current stage name
            substage: Progress within the stage (0.0 to 1.0)
        """
        if stage == "initializing":
            return 2.0 + (substage * 3.0)  # 2-5%
        elif stage == "reasoning":
            # Each turn contributes to progress from 5% to 70%
            turn_progress = min(turn / max(self._estimated_total_turns, 1), 1.0)
            base = 5.0 + (turn_progress * 65.0)
            # Add substage progress within the turn
            turn_range = 65.0 / max(self._estimated_total_turns, 1)
            return base + (substage * turn_range * 0.8)  # 80% of turn range for substages
        elif stage == "generating_report":
            return 70.0 + (substage * 25.0)  # 70-95%
        elif stage == "complete":
            return 100.0
        else:
            return 50.0

    async def process_stream(
        self, stream_generator, callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Process a stream of tokens with timeout handling."""
        content = ""
        try:
            async for token in stream_generator:
                content += token
                if callback:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(token)
                    else:
                        callback(token)

                # Check if we've reached a stop token or end of stream
                for stop_token in self.config.llm.stop_sequence:
                    if stop_token in content:
                        return content
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            logging.error("Error processing stream: %s", str(e))

        return content

    async def execute_action(self, action: Action) -> Tuple[str, Optional[str]]:
        """Execute an action, Return action result and suffix.
        
        This method creates session-isolated tool instances to ensure
        concurrent sessions don't interfere with each other.
        """
        logging.info("Executing action: %s", action.name)

        tool_cls = get_tool(action.name)
        if not tool_cls:
            return f"Error: Tool '{action.name}' not found.", None

        # Create tool instance with session-isolated state
        tool = self._create_session_tool(tool_cls)
        
        try:
            # Add the question as context for tools that need it
            action.arguments["question"] = self.question
            result = ""
            if self.stream_event:
                result = await tool.execute_stream(
                    self.stream_event, self.tool_history, **action.arguments
                )
            else:
                result = await tool.execute(self.tool_history, **action.arguments)

            return result, tool.suffix
        except (ValueError, KeyError, RuntimeError) as e:
            logging.error("Error executing action %s: %s", action.name, str(e))
            return f"Error executing {action.name}: {str(e)}", None
    
    def _create_session_tool(self, tool_cls):
        """Create a tool instance with session-isolated state.
        
        Args:
            tool_cls: The tool class to instantiate.
            
        Returns:
            A tool instance configured with session-specific state.
        """
        tool_name = getattr(tool_cls, 'name', '')
        
        # Pass session-specific state to tools that support it
        if tool_name == 'web_search':
            return tool_cls(
                session_searched_queries=self._session_searched_queries,
                config=self.config
            )
        elif tool_name == 'page_visit':
            return tool_cls(
                session_visited_urls=self._session_visited_urls,
                config=self.config
            )
        else:
            # For other tools, just create a normal instance
            return tool_cls()

    async def run(
        self, on_token: Optional[Callable[[str], None]] = None, is_stream: bool = False
    ) -> str:
        """Run the agent."""
        turn = 0
        
        # Report initial progress
        await self._report_progress(
            self._calculate_progress(0, "initializing", 0.0),
            100.0,
            "Initializing research session..."
        )
        
        await self._report_progress(
            self._calculate_progress(0, "initializing", 0.5),
            100.0,
            "Loading configuration and tools..."
        )
        
        await self._report_progress(
            self._calculate_progress(0, "initializing", 1.0),
            100.0,
            "Ready to begin research..."
        )

        while True:
            # Report reasoning progress - starting to think
            await self._report_progress(
                self._calculate_progress(turn, "reasoning", 0.0),
                100.0,
                f"Turn {turn + 1}: Thinking..."
            )
            
            # Generate streamed completion
            content = ""
            try:
                # Report that we're calling the LLM
                await self._report_progress(
                    self._calculate_progress(turn, "reasoning", 0.1),
                    100.0,
                    f"Turn {turn + 1}: Querying LLM for analysis..."
                )
                
                if is_stream:
                    stream_generator = self.client.generate_completion_stream(
                        self.trace, self.instructions
                    )
                    content = await self.process_stream(stream_generator, on_token)
                else:
                    content = self.client.generate_completion(
                        self.trace, self.instructions
                    )
                
                # Report LLM response received
                await self._report_progress(
                    self._calculate_progress(turn, "reasoning", 0.25),
                    100.0,
                    f"Turn {turn + 1}: Received LLM response, parsing..."
                )
                
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                logging.error("Error generating completion: %s", str(e))
                content = f"Error: {str(e)}"

            turn += 1

            # Parse the output (guard against None from API)
            if content is None:
                content = ""
            try:
                model_output = ModelOutput.from_string(
                    content, tool_names=get_all_tools().keys()
                )
            except (ValueError, KeyError) as e:
                logging.error("Error parsing model output: %s", str(e))
                model_output = ModelOutput(raw=content)

            # Handle normal action/response case
            if model_output.action:
                action_name = model_output.action.name
                logging.info("Processing action: %s", action_name)
                
                # Report tool execution starting
                tool_message = self._get_tool_progress_message(model_output.action)
                await self._report_progress(
                    self._calculate_progress(turn, "reasoning", 0.4),
                    100.0,
                    f"Executing: {tool_message}"
                )

                # Execute the action
                action_result, suffix = await self.execute_action(model_output.action)
                
                # Report tool execution complete
                await self._report_progress(
                    self._calculate_progress(turn, "reasoning", 0.8),
                    100.0,
                    f"Completed: {action_name} - processing results..."
                )

                # Add the turn to the trace
                self.trace.turns.append(
                    Turn(
                        output=model_output, action_result=action_result, suffix=suffix
                    )
                )

            else:
                # Mark this as the last output
                model_output.is_last = True
                self.trace.turns.append(
                    Turn(output=model_output, action_result="", suffix=None)
                )

                # Report report generation progress - multiple stages
                await self._report_progress(
                    self._calculate_progress(turn, "generating_report", 0.0),
                    100.0,
                    "Starting report generation..."
                )
                
                await self._report_progress(
                    self._calculate_progress(turn, "generating_report", 0.2),
                    100.0,
                    "Analyzing gathered information..."
                )

                # Generate the report
                try:
                    report_builder = ReportBuilder(
                        self.stream_event,
                        extra_headers=self._llm_request_headers,
                    )
                    
                    await self._report_progress(
                        self._calculate_progress(turn, "generating_report", 0.4),
                        100.0,
                        "Synthesizing research findings..."
                    )
                    
                    if is_stream:
                        # Stream the report
                        final_report = await report_builder.generate_stream(
                            self.tool_history, self.trace, self.report_type, on_token
                        )
                    else:
                        final_report = report_builder.generate(
                            self.tool_history, self.trace, self.report_type
                        )
                    
                    await self._report_progress(
                        self._calculate_progress(turn, "generating_report", 0.7),
                        100.0,
                        "Formatting report with citations..."
                    )

                    # Create a final turn with the report
                    report_output = ModelOutput(raw=final_report, is_last=True)
                    self.trace.turns.append(
                        Turn(output=report_output, action_result="", suffix=None)
                    )
                    
                    await self._report_progress(
                        self._calculate_progress(turn, "generating_report", 0.9),
                        100.0,
                        "Finalizing report..."
                    )

                    # Report completion
                    await self._report_progress(
                        100.0,
                        100.0,
                        "Research complete"
                    )

                    return final_report

                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    logging.error("Error generating report: %s", str(e))
                    return f"Error generating report: {str(e)}"

            await asyncio.sleep(1)
    
    def _get_tool_progress_message(self, action: Action) -> str:
        """Generate a human-readable progress message for a tool action."""
        tool_name = action.name
        args = action.arguments
        
        if tool_name == "web_search":
            queries = args.get("queries", [])
            if queries:
                return f"Searching: {queries[0][:50]}..."
            return "Performing web search..."
        elif tool_name == "page_visit":
            urls = args.get("urls", [])
            if urls:
                # Extract domain from first URL
                url = urls[0]
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    return f"Visiting: {domain}"
                except:
                    return f"Visiting: {url[:40]}..."
            return "Visiting web pages..."
        else:
            return f"Executing: {tool_name}"
