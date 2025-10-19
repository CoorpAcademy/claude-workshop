"""
Integration tests for cross-collection query generation and execution
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from core.llm_processor import format_schema_for_prompt
from core.mongo_security import validate_aggregation_pipeline, validate_lookup_stage, MongoSecurityError
from core.data_models import FieldRelationship, RelationshipType


@pytest.fixture
def sample_schema_with_relationships():
    """Sample schema including relationships"""
    return {
        "collections": {
            "users": {
                "count": 20,
                "fields": {
                    "id": {"type": "int", "sample": 1},
                    "name": {"type": "str", "sample": "John Doe"},
                    "email": {"type": "str", "sample": "john@example.com"},
                    "city": {"type": "str", "sample": "New York"},
                    "money": {"type": "int", "sample": 850}
                }
            },
            "products": {
                "count": 32,
                "fields": {
                    "product_id": {"type": "int", "sample": 1},
                    "product_name": {"type": "str", "sample": "Laptop Pro 15"},
                    "category": {"type": "str", "sample": "Electronics"},
                    "price": {"type": "float", "sample": 1299.99},
                    "location": {"type": "str", "sample": "New York"}
                }
            }
        },
        "relationships": [
            FieldRelationship(
                source_collection="users",
                source_field="city",
                target_collection="products",
                target_field="location",
                relationship_type=RelationshipType.many_to_many,
                confidence_score=0.85
            )
        ]
    }


def test_format_schema_includes_relationships(sample_schema_with_relationships):
    """Test that formatted schema includes relationship information"""
    formatted = format_schema_for_prompt(sample_schema_with_relationships)

    assert "Relationships between collections:" in formatted
    assert "users.city → products.location" in formatted
    assert "confidence: 0.85" in formatted
    assert "many_to_many" in formatted


def test_valid_lookup_pipeline_validation():
    """Test security validation of valid $lookup pipeline"""
    valid_pipeline = [
        {"$match": {"money": {"$gte": 500}}},
        {"$lookup": {
            "from": "products",
            "localField": "city",
            "foreignField": "location",
            "as": "local_products"
        }},
        {"$match": {"local_products": {"$ne": []}}}
    ]

    # Should not raise any exception
    result = validate_aggregation_pipeline(valid_pipeline)
    assert result == valid_pipeline


def test_valid_lookup_with_pipeline_syntax():
    """Test security validation of $lookup with nested pipeline"""
    valid_pipeline = [
        {"$match": {"money": {"$gte": 500}}},
        {"$lookup": {
            "from": "products",
            "let": {"user_money": "$money"},
            "pipeline": [
                {"$match": {"$expr": {"$lte": ["$price", "$$user_money"]}}},
                {"$match": {"price": {"$gte": 500}}}
            ],
            "as": "affordable_products"
        }}
    ]

    # Should not raise any exception
    result = validate_aggregation_pipeline(valid_pipeline)
    assert result == valid_pipeline


def test_invalid_lookup_missing_from():
    """Test that $lookup without 'from' field is rejected"""
    invalid_lookup = {
        "localField": "city",
        "foreignField": "location",
        "as": "local_products"
    }

    with pytest.raises(MongoSecurityError, match="must have 'from' field"):
        validate_lookup_stage(invalid_lookup)


def test_invalid_lookup_system_collection():
    """Test that $lookup to system collections is blocked"""
    invalid_lookup = {
        "from": "system.users",
        "localField": "user_id",
        "foreignField": "_id",
        "as": "user_info"
    }

    with pytest.raises(MongoSecurityError, match="(cannot reference system collections|cannot start with 'system\\..*reserved)"):
        validate_lookup_stage(invalid_lookup)


def test_invalid_lookup_missing_as():
    """Test that $lookup without 'as' field is rejected"""
    invalid_lookup = {
        "from": "products",
        "localField": "city",
        "foreignField": "location"
    }

    with pytest.raises(MongoSecurityError, match="must have 'as' field"):
        validate_lookup_stage(invalid_lookup)


def test_invalid_lookup_missing_fields():
    """Test that $lookup without localField/foreignField or pipeline is rejected"""
    invalid_lookup = {
        "from": "products",
        "as": "products_list"
    }

    with pytest.raises(MongoSecurityError, match="must have either localField/foreignField or pipeline"):
        validate_lookup_stage(invalid_lookup)


def test_invalid_lookup_dangerous_collection_name():
    """Test that $lookup with invalid collection name is blocked"""
    invalid_lookup = {
        "from": "products$injection",
        "localField": "city",
        "foreignField": "location",
        "as": "products_list"
    }

    with pytest.raises(MongoSecurityError, match="cannot contain.*\\$"):
        validate_lookup_stage(invalid_lookup)


def test_nested_pipeline_validation():
    """Test that nested pipelines in $lookup are validated"""
    lookup_with_dangerous_nested = {
        "from": "products",
        "let": {"user_money": "$money"},
        "pipeline": [
            {"$where": "this.price < user_money"}  # Dangerous $where operator
        ],
        "as": "affordable_products"
    }

    with pytest.raises(MongoSecurityError, match="(Dangerous operator|Unknown or disallowed)"):
        validate_lookup_stage(lookup_with_dangerous_nested)


def test_users_can_afford_products_query_structure():
    """Test structure of users can afford products query"""
    # This would be generated by LLM in real scenario
    query = {
        "query_type": "aggregate",
        "collection": "users",
        "query": [
            {"$match": {"money": {"$gte": 500}}},
            {"$lookup": {
                "from": "products",
                "let": {"user_money": "$money"},
                "pipeline": [
                    {"$match": {"$expr": {"$lte": ["$price", "$$user_money"]}}},
                    {"$match": {"price": {"$gte": 500}}}
                ],
                "as": "affordable_products"
            }},
            {"$match": {"affordable_products": {"$ne": []}}}
        ]
    }

    # Validate pipeline structure
    assert query["query_type"] == "aggregate"
    assert query["collection"] == "users"
    assert len(query["query"]) == 3

    # Validate security
    validate_aggregation_pipeline(query["query"])


def test_products_in_user_cities_query_structure():
    """Test structure of products in user cities query"""
    query = {
        "query_type": "aggregate",
        "collection": "products",
        "query": [
            {"$lookup": {
                "from": "users",
                "localField": "location",
                "foreignField": "city",
                "as": "local_users"
            }},
            {"$match": {"local_users": {"$ne": []}}}
        ]
    }

    # Validate pipeline structure
    assert query["query_type"] == "aggregate"
    assert query["collection"] == "products"
    assert len(query["query"]) == 2

    # Validate security
    validate_aggregation_pipeline(query["query"])


def test_user_product_location_match_query():
    """Test query for users and products in same location"""
    query = {
        "query_type": "aggregate",
        "collection": "users",
        "query": [
            {"$lookup": {
                "from": "products",
                "localField": "city",
                "foreignField": "location",
                "as": "nearby_products"
            }},
            {"$match": {"nearby_products": {"$ne": []}}}
        ]
    }

    # Validate pipeline
    validate_aggregation_pipeline(query["query"])

    # Check structure
    lookup_stage = query["query"][0]["$lookup"]
    assert lookup_stage["from"] == "products"
    assert lookup_stage["localField"] == "city"
    assert lookup_stage["foreignField"] == "location"


def test_multiple_lookup_stages():
    """Test pipeline with multiple $lookup stages"""
    query = [
        {"$lookup": {
            "from": "products",
            "localField": "city",
            "foreignField": "location",
            "as": "nearby_products"
        }},
        {"$lookup": {
            "from": "orders",
            "localField": "id",
            "foreignField": "user_id",
            "as": "user_orders"
        }},
        {"$match": {"nearby_products": {"$ne": []}}}
    ]

    # Should validate successfully
    validate_aggregation_pipeline(query)


def test_complex_cross_collection_with_grouping():
    """Test complex query with lookup and grouping"""
    query = [
        {"$lookup": {
            "from": "products",
            "localField": "city",
            "foreignField": "location",
            "as": "nearby_products"
        }},
        {"$unwind": "$nearby_products"},
        {"$group": {
            "_id": "$city",
            "total_users": {"$sum": 1},
            "total_products": {"$sum": 1}
        }}
    ]

    # Should validate successfully
    validate_aggregation_pipeline(query)


def test_lookup_with_let_variables():
    """Test $lookup with let variables"""
    lookup = {
        "from": "products",
        "let": {
            "user_city": "$city",
            "user_budget": "$money"
        },
        "pipeline": [
            {"$match": {
                "$expr": {
                    "$and": [
                        {"$eq": ["$location", "$$user_city"]},
                        {"$lte": ["$price", "$$user_budget"]}
                    ]
                }
            }}
        ],
        "as": "affordable_nearby_products"
    }

    # Should validate successfully
    validate_lookup_stage(lookup)


def test_empty_result_handling():
    """Test that queries returning empty results are valid"""
    query = [
        {"$match": {"money": {"$gte": 10000}}},  # Very high amount, likely no matches
        {"$lookup": {
            "from": "products",
            "localField": "city",
            "foreignField": "location",
            "as": "nearby_products"
        }}
    ]

    # Should validate successfully even if result will be empty
    validate_aggregation_pipeline(query)
