"""Chat service using Google GenAI and Function Calling."""

import uuid
import json
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.chat.schemas import ChatMessage, ChatResponse
from app.modules.chat.tools import search_activities_tool
from app.modules.activities.service import _activity_to_response
from app.modules.activities.repository import get_by_id, get_coordinates_from_db
from app.modules.activities.spatial import obfuscate_coordinates

# Tool declarations for Gemini
search_tool = {
    "function_declarations": [
        {
            "name": "search_activities",
            "description": "Search for university activities and events based on user preferences. Use this when the user asks for recommendations or wants to find activities.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "semantic_query": {
                        "type": "STRING",
                        "description": "A natural language query representing the semantic meaning of the user's request (e.g. 'activities that grant extracurricular points' or 'events for people without vehicles'). Use this for complex matching.",
                    },
                    "category": {
                        "type": "STRING",
                        "description": "The category of the activity (e.g. sports, academics, social, tech). If not specified, leave empty.",
                    },
                    "keyword": {
                        "type": "STRING",
                        "description": "A search term or keyword to match against activity title and description.",
                    },
                    "radius_meters": {
                        "type": "INTEGER",
                        "description": "Search radius in meters. Default is 10000 (10km).",
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Max number of activities to return. Default is 5.",
                    }
                },
            },
        }
    ]
}


async def handle_chat(
    db: AsyncSession,
    user_id: uuid.UUID,
    messages: list[ChatMessage],
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> ChatResponse:
    """Process a chat using Gemini and execute tool calls if necessary."""
    if not settings.GEMINI_API_KEY:
        return ChatResponse(reply="AI features are currently disabled. Please configure GEMINI_API_KEY.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # We use gemini-2.5-flash which is great for fast function calling
    model_name = "gemini-2.5-flash"

    system_instruction = (
        "You are UniConnect's AI Assistant. Your goal is to help university students discover "
        "relevant activities. Be concise, friendly, and helpful. "
        "When users ask for activity recommendations, ALWAYS use the 'search_activities' tool to fetch real data. "
        "Do not invent activities. Only recommend the ones returned by the tool."
    )

    # Convert messages to Gemini format
    gemini_contents = []
    for msg in messages:
        # Assuming role is 'user' or 'model'
        gemini_contents.append(
            types.Content(role=msg.role, parts=[types.Part.from_text(text=msg.content)])
        )

    # First turn: call the model
    response = client.models.generate_content(
        model=model_name,
        contents=gemini_contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[search_tool],
            temperature=0.7,
        )
    )

    recommended_activities = []

    # If the model decides to call a tool
    if response.function_calls:
        for function_call in response.function_calls:
            if function_call.name == "search_activities":
                # Extract arguments
                args = function_call.args
                category = args.get("category")
                keyword = args.get("keyword")
                semantic_query = args.get("semantic_query")
                radius_meters = args.get("radius_meters", 10000)
                limit = args.get("limit", 5)

                # Execute our internal DB function
                tool_results = await search_activities_tool(
                    db=db,
                    user_id=user_id,
                    category=category,
                    keyword=keyword,
                    semantic_query=semantic_query,
                    lat=user_lat,
                    lng=user_lng,
                    radius_meters=radius_meters,
                    limit=limit
                )
                
                # Fetch full Activity models to return in the API response
                for act_data in tool_results:
                    act_model = await get_by_id(db, uuid.UUID(act_data["id"]))
                    if act_model:
                        coords = await get_coordinates_from_db(db, act_model.id)
                        lat, lng = coords if coords else (0, 0)
                        lat, lng = obfuscate_coordinates(lat, lng)
                        
                        dist = act_data.get("distance_meters")
                        act_resp = _activity_to_response(act_model, lat, lng, distance=dist)
                        recommended_activities.append(act_resp)

                # Send tool response back to the model
                tool_part = types.Part.from_function_response(
                    name="search_activities",
                    response={"activities": tool_results}
                )
                
                # Append model's function call and our response to history
                gemini_contents.append(response.candidates[0].content)
                gemini_contents.append(
                    types.Content(role="user", parts=[tool_part])
                )

                # Second turn: get final answer
                response = client.models.generate_content(
                    model=model_name,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=[search_tool],
                        temperature=0.7,
                    )
                )

    return ChatResponse(
        reply=response.text or "I couldn't generate a response.",
        recommended_activities=recommended_activities if recommended_activities else None
    )
