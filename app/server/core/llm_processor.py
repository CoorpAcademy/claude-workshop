import os
import json
from typing import Dict, Any, Union, List
from openai import OpenAI
from anthropic import Anthropic
from core.data_models import QueryRequest


def generate_mongodb_query_with_openai(query_text: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate MongoDB query using OpenAI API

    Returns a dictionary with:
    - query_type: "find" or "aggregate"
    - collection: collection name
    - query: the actual MongoDB query (filter for find, pipeline for aggregate)
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key)

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following MongoDB collections:

{schema_description}

Convert this natural language query to a MongoDB query: "{query_text}"

You must respond with a valid JSON object in this exact format:
{{
    "query_type": "find" or "aggregate",
    "collection": "collection_name",
    "query": {{}} for find queries OR [] for aggregation pipelines,
    "sort": {{}},
    "limit": number
}}

For simple queries, use "find" with a filter object.
For complex queries (grouping, counting, aggregations), use "aggregate" with a pipeline array.

Examples:

Simple query: "Show all products"
{{
    "query_type": "find",
    "collection": "products",
    "query": {{}},
    "limit": 100
}}

Filter query: "Find products with price greater than 50"
{{
    "query_type": "find",
    "collection": "products",
    "query": {{"price": {{"$gt": 50}}}},
    "limit": 100
}}

Aggregation: "Count users by country"
{{
    "query_type": "aggregate",
    "collection": "users",
    "query": [
        {{"$group": {{"_id": "$country", "count": {{"$sum": 1}}}}}}
    ]
}}

Cross-collection query: "Show me users who can afford products over $500"
{{
    "query_type": "aggregate",
    "collection": "users",
    "query": [
        {{"$match": {{"money": {{"$gte": 500}}}}}},
        {{"$lookup": {{
            "from": "products",
            "let": {{"user_money": "$money"}},
            "pipeline": [
                {{"$match": {{"$expr": {{"$lte": ["$price", "$$user_money"]}}}}}},
                {{"$match": {{"price": {{"$gte": 500}}}}}}
            ],
            "as": "affordable_products"
        }}}},
        {{"$match": {{"affordable_products": {{"$ne": []}}}}}}
    ]
}}

Cross-collection query: "Find products in cities where users live"
{{
    "query_type": "aggregate",
    "collection": "products",
    "query": [
        {{"$lookup": {{
            "from": "users",
            "localField": "location",
            "foreignField": "city",
            "as": "local_users"
        }}}},
        {{"$match": {{"local_users": {{"$ne": []}}}}}}
    ]
}}

MongoDB operators available:
- Comparison: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
- Logical: $and, $or, $not, $nor
- Aggregation stages: $match, $group, $sort, $limit, $project, $count, $lookup
- Aggregation operators: $sum, $avg, $min, $max, $count
- For cross-collection queries: Use $lookup stage in aggregation pipeline

IMPORTANT: When a query requires data from multiple collections, use $lookup in an aggregation pipeline.
Check the "Relationships between collections" section to find valid joins.
Use query_type "aggregate" for cross-collection queries.

Return ONLY the JSON object, no explanations.
"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a MongoDB expert. Convert natural language to MongoDB queries. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        result = json.loads(result_text)

        # Validate result structure
        if "query_type" not in result or "collection" not in result or "query" not in result:
            raise ValueError("Invalid query structure returned from LLM")

        return result

    except Exception as e:
        raise Exception(f"Error generating MongoDB query with OpenAI: {str(e)}")


def generate_mongodb_query_with_anthropic(query_text: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate MongoDB query using Anthropic API

    Returns a dictionary with:
    - query_type: "find" or "aggregate"
    - collection: collection name
    - query: the actual MongoDB query (filter for find, pipeline for aggregate)
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key)

        # Format schema for prompt
        schema_description = format_schema_for_prompt(schema_info)

        # Create prompt
        prompt = f"""Given the following MongoDB collections:

{schema_description}

Convert this natural language query to a MongoDB query: "{query_text}"

You must respond with a valid JSON object in this exact format:
{{
    "query_type": "find" or "aggregate",
    "collection": "collection_name",
    "query": {{}} for find queries OR [] for aggregation pipelines,
    "sort": {{}},
    "limit": number
}}

For simple queries, use "find" with a filter object.
For complex queries (grouping, counting, aggregations), use "aggregate" with a pipeline array.

Examples:

Simple query: "Show all products"
{{
    "query_type": "find",
    "collection": "products",
    "query": {{}},
    "limit": 100
}}

Filter query: "Find products with price greater than 50"
{{
    "query_type": "find",
    "collection": "products",
    "query": {{"price": {{"$gt": 50}}}},
    "limit": 100
}}

Aggregation: "Count users by country"
{{
    "query_type": "aggregate",
    "collection": "users",
    "query": [
        {{"$group": {{"_id": "$country", "count": {{"$sum": 1}}}}}}
    ]
}}

Cross-collection query: "Show me users who can afford products over $500"
{{
    "query_type": "aggregate",
    "collection": "users",
    "query": [
        {{"$match": {{"money": {{"$gte": 500}}}}}},
        {{"$lookup": {{
            "from": "products",
            "let": {{"user_money": "$money"}},
            "pipeline": [
                {{"$match": {{"$expr": {{"$lte": ["$price", "$$user_money"]}}}}}},
                {{"$match": {{"price": {{"$gte": 500}}}}}}
            ],
            "as": "affordable_products"
        }}}},
        {{"$match": {{"affordable_products": {{"$ne": []}}}}}}
    ]
}}

Cross-collection query: "Find products in cities where users live"
{{
    "query_type": "aggregate",
    "collection": "products",
    "query": [
        {{"$lookup": {{
            "from": "users",
            "localField": "location",
            "foreignField": "city",
            "as": "local_users"
        }}}},
        {{"$match": {{"local_users": {{"$ne": []}}}}}}
    ]
}}

MongoDB operators available:
- Comparison: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
- Logical: $and, $or, $not, $nor
- Aggregation stages: $match, $group, $sort, $limit, $project, $count, $lookup
- Aggregation operators: $sum, $avg, $min, $max, $count
- For cross-collection queries: Use $lookup stage in aggregation pipeline

IMPORTANT: When a query requires data from multiple collections, use $lookup in an aggregation pipeline.
Check the "Relationships between collections" section to find valid joins.
Use query_type "aggregate" for cross-collection queries.

Return ONLY the JSON object, no explanations.
"""

        # Call Anthropic API
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text.strip()

        # Clean up markdown if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        # Parse JSON response
        result = json.loads(result_text.strip())

        # Validate result structure
        if "query_type" not in result or "collection" not in result or "query" not in result:
            raise ValueError("Invalid query structure returned from LLM")

        return result

    except Exception as e:
        raise Exception(f"Error generating MongoDB query with Anthropic: {str(e)}")


def format_schema_for_prompt(schema_info: Dict[str, Any], relationships: List[Any] = None) -> str:
    """
    Format MongoDB database schema for LLM prompt, including relationship information
    """
    lines = []

    # Handle new format where schema_info might have 'collections' key
    collections = schema_info.get('collections', schema_info)
    if relationships is None:
        relationships = schema_info.get('relationships', [])

    for collection_name, collection_info in collections.items():
        lines.append(f"Collection: {collection_name}")
        lines.append(f"Document count: {collection_info.get('count', 0)}")
        lines.append("Fields:")

        fields = collection_info.get('fields', {})
        for field_name, field_info in fields.items():
            field_type = field_info.get('type', 'unknown')
            sample = field_info.get('sample', '')
            if field_name != '_id':
                lines.append(f"  - {field_name} ({field_type}) - example: {sample}")

        lines.append("")

    # Add relationships section
    if relationships and len(relationships) > 0:
        lines.append("Relationships between collections:")
        for rel in relationships:
            # Handle both dict and object formats
            if hasattr(rel, 'source_collection'):
                lines.append(
                    f"  - {rel.source_collection}.{rel.source_field} → "
                    f"{rel.target_collection}.{rel.target_field} "
                    f"(confidence: {rel.confidence_score:.2f}, type: {rel.relationship_type.value})"
                )
            else:
                lines.append(
                    f"  - {rel.get('source_collection')}.{rel.get('source_field')} → "
                    f"{rel.get('target_collection')}.{rel.get('target_field')} "
                    f"(confidence: {rel.get('confidence_score', 0):.2f}, type: {rel.get('relationship_type', 'unknown')})"
                )
        lines.append("")

    return "\n".join(lines)


def generate_mongodb_query(request: QueryRequest, schema_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route to appropriate LLM provider based on API key availability and request preference.
    Priority: 1) OpenAI API key exists, 2) Anthropic API key exists, 3) request.llm_provider
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # Check API key availability first (OpenAI priority)
    if openai_key:
        return generate_mongodb_query_with_openai(request.query, schema_info)
    elif anthropic_key:
        return generate_mongodb_query_with_anthropic(request.query, schema_info)

    # Fall back to request preference if both keys available or neither available
    if request.llm_provider == "openai":
        return generate_mongodb_query_with_openai(request.query, schema_info)
    else:
        return generate_mongodb_query_with_anthropic(request.query, schema_info)
