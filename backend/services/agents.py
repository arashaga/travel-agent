from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict

from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion,AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments
from ..settings.instructions import (
    FLIGHT_AGENT_NAME,
    FLIGHT_AGENT_INSTRUCTIONS,
    HOTEL_AGENT_NAME,
    HOTEL_AGENT_INSTRUCTIONS,
    COORDINATOR_AGENT_NAME,
    COORDINATOR_AGENT_INSTRUCTIONS,
)
from ..settings.config import (
    deployment_name,
    endpoint,
    api_key,
    api_version,
    serpapi_api_key,
)
from ..plugins.flight_plugin import FlightSearchPlugin
from ..plugins.hotel_plugin import HotelSearchPlugin

# def _default_exec_settings() -> AzureChatPromptExecutionSettings:
#     # Encourage the model to call functions when relevant
#     return AzureChatPromptExecutionSettings(
#         temperature=0.2,
#         max_tokens=1500,
#         function_choice_behavior=FunctionChoiceBehavior.Auto()  # <-- key line
#     )
# def _create_azure_chat_completion(service_id: str) -> AzureChatCompletion:

#     return AzureChatCompletion(
#         service_id=service_id,
#         deployment_name=deployment_name,
#         endpoint=endpoint,
#         api_key=api_key,
#         api_version=api_version,
#     )
# ADD THIS helper
def _build_agent_with_kernel(
    service_id: str,
    name: str,
    instructions: str,
    plugin_obj=None,
    plugin_name: str | None = None,
) -> ChatCompletionAgent:
    # Create a kernel for this agent
    k = Kernel()
    # Attach the AzureChatCompletion service with a unique service_id
    k.add_service(
        AzureChatCompletion(
            service_id=service_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
    )
    # Register the plugin (scoped to this agent's kernel) if provided
    if plugin_obj is not None and plugin_name:
        k.add_plugin(plugin_obj, plugin_name=plugin_name)

    # Pull settings from the kernel and enable auto function calling
    settings = k.get_prompt_execution_settings_from_service_id(service_id=service_id)
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Construct the agent with Kernel + KernelArguments(settings=...)
    return ChatCompletionAgent(
        kernel=k,
        name=name,
        instructions=instructions,
        arguments=KernelArguments(settings=settings),
    )


class TravelPlanningTerminationStrategy(TerminationStrategy):
    def __init__(self, agents, maximum_iterations: int = 1):
        super().__init__(agents=agents, maximum_iterations=maximum_iterations)

    def _get_completion_keywords(self):
        return [
            "travel plan complete",
            "recommendations finalized",
            "trip confirmed",
            "all set",
            "that’s all i need",
            "planning session finished",
            "conversation ended",
            "that's all for now",
            "thank you goodbye",
            "planning is done",
        ]

    async def should_agent_terminate(self, agent, history):
        if not history:
            return False
        last_message = (history[-1].content or "").lower()
        for keyword in self._get_completion_keywords():
            if keyword in last_message:
                return True
        if "?" in last_message:
            return False
        return False


def _create_agents():
    flight_plugin = FlightSearchPlugin()
    hotel_plugin = HotelSearchPlugin()

    flight_agent = _build_agent_with_kernel(
        service_id="flight_specialist",
        name=FLIGHT_AGENT_NAME,
        instructions=FLIGHT_AGENT_INSTRUCTIONS,
        plugin_obj=flight_plugin,
        plugin_name="flight",   # plugin name shown to the model
    )
    hotel_agent = _build_agent_with_kernel(
        service_id="hotel_specialist",
        name=HOTEL_AGENT_NAME,
        instructions=HOTEL_AGENT_INSTRUCTIONS,
        plugin_obj=hotel_plugin,
        plugin_name="hotel",   # plugin name shown to the model
    )
    coordinator_agent = _build_agent_with_kernel(
        service_id="travel_coordinator",
        name=COORDINATOR_AGENT_NAME,
        instructions=COORDINATOR_AGENT_INSTRUCTIONS,
    )
    return flight_agent, hotel_agent, coordinator_agent


def _create_group_chat():
    flight_agent, hotel_agent, coordinator_agent = _create_agents()
    termination_strategy = TravelPlanningTerminationStrategy(
    agents=[coordinator_agent], maximum_iterations=1
    )
    group = AgentGroupChat(
        agents=[coordinator_agent, flight_agent, hotel_agent],
        termination_strategy=termination_strategy,
    )
    return group


class TravelConversationManager:
    def __init__(self):
        # Maintain a separate AgentGroupChat per session id
        self._sessions: Dict[str, AgentGroupChat] = {}

    def reset_conversation(self, session_id: str):
        # Remove a specific session's conversation
        if session_id in self._sessions:
            del self._sessions[session_id]

    def _ensure(self, session_id: str) -> AgentGroupChat:
        # Create if missing and return the session's group chat
        if session_id not in self._sessions:
            self._sessions[session_id] = _create_group_chat()
        return self._sessions[session_id]

    async def send_message(self, session_id: str, message: str, verbose: bool = False) -> List[str]:
        group_chat = self._ensure(session_id)
        await group_chat.add_chat_message(message=message)
        responses: List[str] = []
        async for content in group_chat.invoke():
            responses.append(f"**{content.name}**: {content.content}")
        return responses


class TravelConversationManagerFactory:
    @staticmethod
    def create() -> TravelConversationManager:
        load_dotenv()
        # Validate required Azure OpenAI settings
        missing = [k for k, v in {
            "GRAPHRAG_LLM_MODEL": deployment_name,
            "GRAPHRAG_API_BASE": endpoint,
            "GRAPHRAG_API_KEY": api_key,
            "SERPAPI_API_KEY": serpapi_api_key,
        }.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing Azure OpenAI configuration values: {', '.join(missing)}. Check your .env."
            )
        return TravelConversationManager()
