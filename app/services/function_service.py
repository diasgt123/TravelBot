from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.config import get_settings
from typing import Dict, Any
import json

settings = get_settings()

class FunctionService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=settings.MODEL_NAME,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create tools for the agent to use"""
        return [
            Tool(
                name="book_trip",
                func=self._book_trip,
                description="Book a trip to a specific destination. Input should be a JSON string with 'destination' field."
            ),
            Tool(
                name="get_itinerary",
                func=self._get_itinerary,
                description="Get the itinerary for a booked trip. Input should be a JSON string with 'trip_id' field."
            ),
            Tool(
                name="check_visa_requirements",
                func=self._check_visa_requirements,
                description="Check visa requirements for a destination. Input should be a JSON string with 'destination' field."
            )
        ]
    
    def _create_agent(self):
        """Create the agent with tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful travel assistant. Use the provided tools to help users with their travel needs."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Process a message and determine if function calling is needed"""
        try:
            result = await self.agent.ainvoke({
                "input": message,
                "chat_history": []  # You might want to load this from Redis
            })
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _book_trip(self, input_str: str) -> str:
        """Book a trip to a destination"""
        try:
            data = json.loads(input_str)
            destination = data.get("destination")
            # Here you would integrate with a real booking system
            return f"Booking page for {destination}: https://example.com/book/{destination}"
        except Exception as e:
            return f"Error booking trip: {str(e)}"
    
    def _get_itinerary(self, input_str: str) -> str:
        """Get itinerary for a booked trip"""
        try:
            data = json.loads(input_str)
            trip_id = data.get("trip_id")
            # Here you would fetch from a real booking system
            return f"Itinerary for trip {trip_id}: https://example.com/itinerary/{trip_id}"
        except Exception as e:
            return f"Error getting itinerary: {str(e)}"
    
    def _check_visa_requirements(self, input_str: str) -> str:
        """Check visa requirements for a destination"""
        try:
            data = json.loads(input_str)
            destination = data.get("destination")
            # Here you would integrate with a visa information service
            return f"Visa requirements for {destination}: https://example.com/visa/{destination}"
        except Exception as e:
            return f"Error checking visa requirements: {str(e)}" 