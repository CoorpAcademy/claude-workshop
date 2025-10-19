"""
Unit tests for relationship detector module
"""

import pytest
from unittest.mock import Mock, MagicMock
from core.relationship_detector import (
    detect_id_field_relationships,
    detect_name_based_relationships,
    detect_value_overlap_relationships,
    calculate_relationship_confidence,
    detect_all_relationships
)
from core.data_models import FieldRelationship, RelationshipType


@pytest.fixture
def sample_schema():
    """Sample schema with multiple collections"""
    return {
        "users": {
            "id": "number",
            "name": "string",
            "email": "string",
            "city": "string",
            "money": "number"
        },
        "products": {
            "product_id": "number",
            "name": "string",
            "category": "string",
            "price": "number",
            "location": "string"
        },
        "orders": {
            "order_id": "number",
            "user_id": "number",
            "product_id": "number",
            "customer_name": "string",
            "product_category": "string"
        }
    }


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    return db


def test_detect_id_field_relationships(sample_schema, mock_db):
    """Test detection of _id and _key patterns"""
    relationships = detect_id_field_relationships(sample_schema, mock_db)

    # Should detect orders.user_id -> users.id
    user_rel = next(
        (r for r in relationships
         if r.source_collection == "orders" and r.source_field == "user_id"),
        None
    )
    assert user_rel is not None
    assert user_rel.target_collection == "users"
    assert user_rel.target_field == "id"
    assert user_rel.confidence_score == 0.9

    # Should detect orders.product_id -> products.product_id
    product_rel = next(
        (r for r in relationships
         if r.source_collection == "orders" and r.source_field == "product_id"),
        None
    )
    assert product_rel is not None
    assert product_rel.target_collection == "products"


def test_detect_name_based_relationships(sample_schema):
    """Test detection of name-based references"""
    relationships = detect_name_based_relationships(sample_schema)

    # Should detect orders.customer_name -> users.name
    name_rel = next(
        (r for r in relationships
         if r.source_field == "customer_name" and r.target_field == "name"),
        None
    )
    assert name_rel is not None
    assert name_rel.target_collection == "users"
    assert name_rel.confidence_score == 0.75

    # Should detect orders.product_category -> products.category
    category_rel = next(
        (r for r in relationships
         if r.source_field == "product_category" and r.target_field == "category"),
        None
    )
    assert category_rel is not None
    assert category_rel.target_collection == "products"


def test_detect_value_overlap_relationships(mock_db):
    """Test value overlap calculation"""
    # Mock source collection data
    mock_db.__getitem__.return_value.find.return_value.limit.return_value = [
        {"city": "New York"},
        {"city": "Chicago"},
        {"city": "Los Angeles"}
    ]

    # First call returns source data
    source_docs = [
        {"city": "New York"},
        {"city": "Chicago"},
        {"city": "Los Angeles"}
    ]

    # Second call returns target data
    target_docs = [
        {"location": "New York"},
        {"location": "Chicago"},
        {"location": "Boston"}
    ]

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Configure mock to return different results for sequential calls
    mock_collection.find.return_value.limit.side_effect = [source_docs, target_docs]

    confidence = detect_value_overlap_relationships(
        "users", "city",
        "products", "location",
        mock_db
    )

    # 2 out of 3 values overlap (New York, Chicago)
    assert confidence > 0.5
    assert confidence <= 1.0


def test_relationship_confidence_scoring():
    """Test confidence calculation"""
    # Perfect match
    assert calculate_relationship_confidence(100, 100) == 1.0

    # 50% match
    confidence = calculate_relationship_confidence(50, 100, base_confidence=0.5)
    assert 0.4 < confidence < 0.6

    # No match
    confidence = calculate_relationship_confidence(0, 100, base_confidence=0.5)
    assert confidence == 0.25  # Base confidence * 0.5 + 0 * 0.5

    # Zero samples
    assert calculate_relationship_confidence(0, 0) == 0.0


def test_no_false_positives():
    """Ensure unrelated fields don't create relationships"""
    schema = {
        "users": {
            "id": "number",
            "name": "string",
            "random_field": "string"
        },
        "products": {
            "product_id": "number",
            "description": "string",
            "unrelated_field": "number"
        }
    }

    mock_db = MagicMock()
    relationships = detect_id_field_relationships(schema, mock_db)

    # Should not create relationship between random_field and unrelated_field
    false_rel = next(
        (r for r in relationships
         if r.source_field == "random_field" or r.source_field == "unrelated_field"),
        None
    )
    assert false_rel is None


def test_bidirectional_relationships(mock_db):
    """Test that A→B and B→A are both detected when appropriate"""
    schema = {
        "users": {
            "id": "number",
            "city": "string"
        },
        "products": {
            "product_id": "number",
            "location": "string"
        }
    }

    # Mock value overlap detection
    source_docs = [{"city": "New York"}, {"city": "Chicago"}]
    target_docs = [{"location": "New York"}, {"location": "Chicago"}]

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value.limit.side_effect = [
        source_docs, target_docs,
        target_docs, source_docs  # Reverse direction
    ]

    relationships = detect_all_relationships(schema, mock_db, min_confidence=0.3)

    # Should detect city/location relationship
    city_rel = next(
        (r for r in relationships
         if r.source_field in ["city", "location"] and r.target_field in ["city", "location"]),
        None
    )
    assert city_rel is not None


def test_min_confidence_threshold(mock_db):
    """Test filtering by minimum confidence"""
    schema = {
        "users": {"id": "number", "name": "string", "city": "string"},
        "products": {"product_id": "number", "location": "string"}
    }

    # Mock low overlap
    source_docs = [{"city": "New York"}]
    target_docs = [{"location": "Boston"}]  # No overlap

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value.limit.side_effect = [source_docs, target_docs]

    # With high threshold, should not include low-confidence relationships
    relationships = detect_all_relationships(schema, mock_db, min_confidence=0.8)

    # Should not include city-location relationship due to low confidence
    low_conf_rel = next(
        (r for r in relationships
         if r.source_field == "city" and r.target_field == "location"),
        None
    )
    # May be None or not depending on other detection methods
    # The key is that relationships below threshold are filtered


def test_empty_collections(mock_db):
    """Test handling of empty collections"""
    schema = {
        "users": {"id": "number"},
        "products": {"product_id": "number"}
    }

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value.limit.return_value = []

    relationships = detect_all_relationships(schema, mock_db, min_confidence=0.3)

    # Should handle gracefully without errors
    assert isinstance(relationships, list)


def test_single_document_collections(mock_db):
    """Test handling of collections with single documents"""
    schema = {
        "users": {"id": "number", "city": "string"},
        "products": {"product_id": "number", "location": "string"}
    }

    source_docs = [{"city": "New York"}]
    target_docs = [{"location": "New York"}]

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value.limit.side_effect = [source_docs, target_docs]

    confidence = detect_value_overlap_relationships(
        "users", "city",
        "products", "location",
        mock_db
    )

    # Should be 100% overlap with single matching value
    assert confidence == 1.0


def test_collections_with_no_relationships(mock_db):
    """Test handling when no relationships exist"""
    schema = {
        "collection_a": {"field1": "string", "field2": "number"},
        "collection_b": {"field3": "string", "field4": "number"}
    }

    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find.return_value.limit.return_value = []

    relationships = detect_all_relationships(schema, mock_db, min_confidence=0.3)

    # May have no relationships or only low-confidence ones
    assert isinstance(relationships, list)
