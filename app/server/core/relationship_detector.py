"""
Relationship Detection Module

This module automatically detects relationships between MongoDB collections
by analyzing field names, data types, and value overlaps.
"""

from typing import Dict, List, Any, Set, Optional
from core.data_models import FieldRelationship, RelationshipType
from pymongo import MongoClient
from pymongo.database import Database
import logging

logger = logging.getLogger(__name__)


def detect_id_field_relationships(
    schema_info: Dict[str, Dict[str, str]],
    db: Database
) -> List[FieldRelationship]:
    """
    Detect relationships based on field names ending in _id, _key,
    or matching exact collection names.

    Args:
        schema_info: Dictionary mapping collection names to field schemas
        db: MongoDB database instance

    Returns:
        List of detected field relationships
    """
    relationships = []

    for source_collection, fields in schema_info.items():
        for field_name, field_type in fields.items():
            # Check for _id pattern
            if field_name.endswith('_id') and field_name != '_id':
                potential_target = field_name[:-3]  # Remove '_id' suffix

                # Try exact match first
                target_collection = None
                if potential_target in schema_info:
                    target_collection = potential_target
                # Try plural form
                elif potential_target + 's' in schema_info:
                    target_collection = potential_target + 's'
                # Try singular form (remove trailing 's')
                elif potential_target.endswith('s') and potential_target[:-1] in schema_info:
                    target_collection = potential_target[:-1]

                if target_collection:
                    # Look for matching ID field in target collection
                    target_field = None
                    if 'id' in schema_info[target_collection]:
                        target_field = 'id'
                    elif field_name in schema_info[target_collection]:
                        target_field = field_name  # Same field name in target
                    elif potential_target + '_id' in schema_info[target_collection]:
                        target_field = potential_target + '_id'

                    if target_field:
                        relationships.append(FieldRelationship(
                            source_collection=source_collection,
                            source_field=field_name,
                            target_collection=target_collection,
                            target_field=target_field,
                            relationship_type=RelationshipType.one_to_many,
                            confidence_score=0.9
                        ))

            # Check for collection name pattern (e.g., 'user' field when 'users' collection exists)
            for potential_target in schema_info.keys():
                if potential_target != source_collection:
                    # Check singular/plural matching
                    if (field_name == potential_target or
                        field_name == potential_target.rstrip('s') or
                        field_name + 's' == potential_target):
                        relationships.append(FieldRelationship(
                            source_collection=source_collection,
                            source_field=field_name,
                            target_collection=potential_target,
                            target_field='id' if 'id' in schema_info[potential_target] else '_id',
                            relationship_type=RelationshipType.one_to_many,
                            confidence_score=0.7
                        ))

    return relationships


def detect_name_based_relationships(
    schema_info: Dict[str, Dict[str, str]]
) -> List[FieldRelationship]:
    """
    Detect relationships where field names suggest references.
    For example, 'customer_name' might reference 'users.name'.

    Args:
        schema_info: Dictionary mapping collection names to field schemas

    Returns:
        List of detected field relationships
    """
    relationships = []

    # Common synonyms for entities
    synonyms = {
        'customer': 'user',
        'client': 'user',
        'item': 'product',
        'good': 'product',
    }

    for source_collection, fields in schema_info.items():
        for field_name, field_type in fields.items():
            # Look for patterns like 'customer_name', 'user_email', etc.
            if '_' in field_name:
                parts = field_name.split('_')
                potential_target_prefix = parts[0]  # e.g., 'customer', 'user', 'product'
                field_suffix = '_'.join(parts[1:])  # e.g., 'name', 'email', 'id'

                # Check synonyms
                if potential_target_prefix in synonyms:
                    potential_target_prefix = synonyms[potential_target_prefix]

                # Check if there's a collection matching the prefix
                for potential_target in schema_info.keys():
                    if (potential_target.startswith(potential_target_prefix) or
                        potential_target.rstrip('s') == potential_target_prefix):
                        # Check if the target collection has the referenced field
                        if field_suffix in schema_info[potential_target]:
                            relationships.append(FieldRelationship(
                                source_collection=source_collection,
                                source_field=field_name,
                                target_collection=potential_target,
                                target_field=field_suffix,
                                relationship_type=RelationshipType.one_to_many,
                                confidence_score=0.75
                            ))

    return relationships


def detect_value_overlap_relationships(
    source_collection: str,
    source_field: str,
    target_collection: str,
    target_field: str,
    db: Database,
    sample_size: int = 100
) -> float:
    """
    Calculate value overlap percentage between two fields by sampling data.

    Args:
        source_collection: Name of the source collection
        source_field: Name of the field in source collection
        target_collection: Name of the target collection
        target_field: Name of the field in target collection
        db: MongoDB database instance
        sample_size: Number of documents to sample

    Returns:
        Confidence score between 0.0 and 1.0 based on value overlap
    """
    try:
        # Sample values from source collection
        source_docs = list(db[source_collection].find(
            {source_field: {"$exists": True, "$ne": None}},
            {source_field: 1, "_id": 0}
        ).limit(sample_size))

        if not source_docs:
            return 0.0

        source_values = {doc.get(source_field) for doc in source_docs if doc.get(source_field) is not None}

        if not source_values:
            return 0.0

        # Sample values from target collection
        target_docs = list(db[target_collection].find(
            {target_field: {"$exists": True, "$ne": None}},
            {target_field: 1, "_id": 0}
        ).limit(sample_size))

        if not target_docs:
            return 0.0

        target_values = {doc.get(target_field) for doc in target_docs if doc.get(target_field) is not None}

        if not target_values:
            return 0.0

        # Calculate overlap
        overlap = source_values.intersection(target_values)
        overlap_ratio = len(overlap) / len(source_values)

        return min(overlap_ratio, 1.0)

    except Exception as e:
        logger.error(f"Error calculating value overlap: {e}")
        return 0.0


def calculate_relationship_confidence(
    matches: int,
    total_samples: int,
    base_confidence: float = 0.0
) -> float:
    """
    Calculate confidence score based on value overlap.

    Args:
        matches: Number of matching values
        total_samples: Total number of samples checked
        base_confidence: Base confidence score (default 0.0 means use overlap ratio only)

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if total_samples == 0:
        return 0.0

    overlap_ratio = matches / total_samples

    # If base_confidence is 0, use overlap ratio directly
    if base_confidence == 0.0:
        return min(max(overlap_ratio, 0.0), 1.0)

    # Otherwise combine base confidence with overlap ratio
    confidence = base_confidence * 0.5 + overlap_ratio * 0.5

    return min(max(confidence, 0.0), 1.0)


def detect_all_relationships(
    schema_info: Dict[str, Dict[str, str]],
    db: Database,
    min_confidence: float = 0.3
) -> List[FieldRelationship]:
    """
    Main function that orchestrates all detection methods.

    Args:
        schema_info: Dictionary mapping collection names to field schemas
        db: MongoDB database instance
        min_confidence: Minimum confidence threshold for relationships

    Returns:
        List of detected field relationships above confidence threshold
    """
    all_relationships = []
    seen_pairs = set()  # Track unique (source_collection, source_field, target_collection, target_field)

    # Detect ID-based relationships
    id_relationships = detect_id_field_relationships(schema_info, db)
    for rel in id_relationships:
        pair_key = (rel.source_collection, rel.source_field, rel.target_collection, rel.target_field)
        if pair_key not in seen_pairs and rel.confidence_score >= min_confidence:
            all_relationships.append(rel)
            seen_pairs.add(pair_key)

    # Detect name-based relationships
    name_relationships = detect_name_based_relationships(schema_info)
    for rel in name_relationships:
        pair_key = (rel.source_collection, rel.source_field, rel.target_collection, rel.target_field)
        if pair_key not in seen_pairs:
            # Verify with value overlap
            overlap_confidence = detect_value_overlap_relationships(
                rel.source_collection,
                rel.source_field,
                rel.target_collection,
                rel.target_field,
                db
            )

            # Update confidence based on value overlap
            if overlap_confidence > 0.2:  # At least 20% overlap
                rel.confidence_score = (rel.confidence_score + overlap_confidence) / 2
                if rel.confidence_score >= min_confidence:
                    all_relationships.append(rel)
                    seen_pairs.add(pair_key)

    # Detect common field name overlaps (like 'city', 'location', 'category')
    common_fields = ['city', 'location', 'category', 'name', 'email', 'status']
    for common_field in common_fields:
        collections_with_field = [
            coll for coll, fields in schema_info.items()
            if common_field in fields
        ]

        if len(collections_with_field) >= 2:
            # Check pairwise relationships
            for i, source_coll in enumerate(collections_with_field):
                for target_coll in collections_with_field[i+1:]:
                    pair_key = (source_coll, common_field, target_coll, common_field)
                    reverse_pair_key = (target_coll, common_field, source_coll, common_field)

                    if pair_key not in seen_pairs and reverse_pair_key not in seen_pairs:
                        # Check value overlap
                        overlap_confidence = detect_value_overlap_relationships(
                            source_coll,
                            common_field,
                            target_coll,
                            common_field,
                            db
                        )

                        if overlap_confidence >= min_confidence:
                            all_relationships.append(FieldRelationship(
                                source_collection=source_coll,
                                source_field=common_field,
                                target_collection=target_coll,
                                target_field=common_field,
                                relationship_type=RelationshipType.many_to_many,
                                confidence_score=overlap_confidence
                            ))
                            seen_pairs.add(pair_key)

    logger.info(f"Detected {len(all_relationships)} relationships across {len(schema_info)} collections")

    return all_relationships
