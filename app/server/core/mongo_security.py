"""
MongoDB Security Module

This module provides security validation for MongoDB operations to prevent NoSQL injection
and other security vulnerabilities. It validates collection names, field names, query structures,
and regex patterns to ensure safe MongoDB operations.
"""

import re
from typing import Any, Dict, List

class MongoSecurityError(Exception):
    """Exception raised for MongoDB security violations"""
    pass


def validate_collection_name(collection_name: str) -> str:
    """
    Validate MongoDB collection name to prevent injection attacks.

    MongoDB collection names:
    - Cannot be empty
    - Cannot contain null characters
    - Cannot start with "system." (reserved)
    - Cannot contain "$" (reserved for internal use)
    - Should only contain alphanumeric characters, underscores, and hyphens

    Args:
        collection_name: The collection name to validate

    Returns:
        The validated collection name

    Raises:
        MongoSecurityError: If the collection name is invalid
    """
    if not collection_name:
        raise MongoSecurityError("Collection name cannot be empty")

    if len(collection_name) > 120:
        raise MongoSecurityError("Collection name is too long (max 120 characters)")

    if '\x00' in collection_name:
        raise MongoSecurityError("Collection name cannot contain null characters")

    if collection_name.startswith("system."):
        raise MongoSecurityError("Collection name cannot start with 'system.' (reserved namespace)")

    if "$" in collection_name:
        raise MongoSecurityError("Collection name cannot contain '$' character")

    # Allow only alphanumeric, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', collection_name):
        raise MongoSecurityError(
            "Collection name can only contain letters, numbers, underscores, and hyphens"
        )

    return collection_name


def validate_field_name(field_name: str) -> str:
    """
    Validate MongoDB field name to prevent injection attacks.

    MongoDB field names:
    - Cannot be empty
    - Cannot contain null characters
    - Cannot start with "$" (reserved for operators)
    - Should not contain "." in regular queries (used for nested fields)

    Args:
        field_name: The field name to validate

    Returns:
        The validated field name

    Raises:
        MongoSecurityError: If the field name is invalid
    """
    if not field_name:
        raise MongoSecurityError("Field name cannot be empty")

    if '\x00' in field_name:
        raise MongoSecurityError("Field name cannot contain null characters")

    # Allow "." for nested field access but validate each part
    parts = field_name.split(".")
    for part in parts:
        if not part:
            raise MongoSecurityError("Field name parts cannot be empty")

        if part.startswith("$"):
            raise MongoSecurityError(f"Field name part cannot start with '$': {part}")

    return field_name


def validate_query_structure(query: Dict[str, Any], allow_operators: bool = True) -> Dict[str, Any]:
    """
    Validate MongoDB query structure to prevent NoSQL injection.

    This function recursively validates query structures to ensure they don't contain
    dangerous operations like $where with JavaScript code execution.

    Args:
        query: The MongoDB query dictionary to validate
        allow_operators: Whether to allow MongoDB operators like $gt, $lt, etc.

    Returns:
        The validated query dictionary

    Raises:
        MongoSecurityError: If the query contains dangerous operations
    """
    if not isinstance(query, dict):
        raise MongoSecurityError("Query must be a dictionary")

    dangerous_operators = ["$where"]

    for key, value in query.items():
        # Check for dangerous operators
        if key in dangerous_operators:
            raise MongoSecurityError(f"Dangerous operator not allowed: {key}")

        # Validate MongoDB operators
        if key.startswith("$"):
            if not allow_operators:
                raise MongoSecurityError(f"Operators not allowed in this context: {key}")

            # List of allowed operators
            allowed_operators = [
                "$eq", "$ne", "$gt", "$gte", "$lt", "$lte",
                "$in", "$nin", "$and", "$or", "$not", "$nor",
                "$exists", "$type", "$regex", "$options",
                "$all", "$elemMatch", "$size",
                "$mod", "$text", "$search"
            ]

            if key not in allowed_operators:
                raise MongoSecurityError(f"Unknown or disallowed operator: {key}")
        else:
            # Validate field names (non-operator keys)
            validate_field_name(key)

        # Recursively validate nested structures
        if isinstance(value, dict):
            validate_query_structure(value, allow_operators=True)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    validate_query_structure(item, allow_operators=True)


def validate_lookup_stage(lookup_stage: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate MongoDB $lookup stage to prevent security issues.

    Args:
        lookup_stage: The $lookup stage configuration

    Returns:
        The validated lookup stage

    Raises:
        MongoSecurityError: If the $lookup stage is invalid or dangerous
    """
    if not isinstance(lookup_stage, dict):
        raise MongoSecurityError("$lookup stage must be a dictionary")

    # Validate 'from' collection
    if "from" not in lookup_stage:
        raise MongoSecurityError("$lookup stage must have 'from' field")

    from_collection = lookup_stage["from"]
    validate_collection_name(from_collection)

    # Prevent lookup from system collections
    if from_collection.startswith("system."):
        raise MongoSecurityError("$lookup cannot reference system collections")

    # Validate 'as' field
    if "as" not in lookup_stage:
        raise MongoSecurityError("$lookup stage must have 'as' field")

    as_field = lookup_stage["as"]
    if not isinstance(as_field, str) or not as_field:
        raise MongoSecurityError("$lookup 'as' field must be a non-empty string")

    validate_field_name(as_field)

    # Validate localField/foreignField or pipeline syntax
    if "localField" in lookup_stage or "foreignField" in lookup_stage:
        # Simple equality match syntax
        if "localField" in lookup_stage:
            validate_field_name(lookup_stage["localField"])
        if "foreignField" in lookup_stage:
            validate_field_name(lookup_stage["foreignField"])
    elif "pipeline" in lookup_stage:
        # Pipeline syntax - validate the nested pipeline
        nested_pipeline = lookup_stage["pipeline"]
        if not isinstance(nested_pipeline, list):
            raise MongoSecurityError("$lookup 'pipeline' must be a list")

        # Recursively validate nested pipeline
        validate_aggregation_pipeline(nested_pipeline)

        # Validate 'let' variables if present
        if "let" in lookup_stage:
            let_vars = lookup_stage["let"]
            if not isinstance(let_vars, dict):
                raise MongoSecurityError("$lookup 'let' must be a dictionary")
            for var_name in let_vars.keys():
                if not var_name or not isinstance(var_name, str):
                    raise MongoSecurityError("$lookup 'let' variable names must be non-empty strings")
    else:
        raise MongoSecurityError("$lookup must have either localField/foreignField or pipeline")

    return lookup_stage


def validate_aggregation_pipeline(pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate MongoDB aggregation pipeline to prevent security issues.

    Args:
        pipeline: List of aggregation stage dictionaries

    Returns:
        The validated pipeline

    Raises:
        MongoSecurityError: If the pipeline contains dangerous operations
    """
    if not isinstance(pipeline, list):
        raise MongoSecurityError("Aggregation pipeline must be a list")

    dangerous_stages = ["$function", "$accumulator"]

    allowed_stages = [
        "$match", "$group", "$project", "$sort", "$limit", "$skip",
        "$unwind", "$lookup", "$addFields", "$count", "$sortByCount",
        "$facet", "$bucket", "$bucketAuto", "$sample", "$replaceRoot",
        "$out", "$merge", "$geoNear", "$graphLookup", "$redact",
        "$replaceWith", "$set", "$unset"
    ]

    for stage in pipeline:
        if not isinstance(stage, dict):
            raise MongoSecurityError("Each aggregation stage must be a dictionary")

        if len(stage) != 1:
            raise MongoSecurityError("Each aggregation stage must have exactly one operator")

        stage_name = list(stage.keys())[0]

        if stage_name in dangerous_stages:
            raise MongoSecurityError(f"Dangerous aggregation stage not allowed: {stage_name}")

        if not stage_name.startswith("$"):
            raise MongoSecurityError(f"Invalid aggregation stage (must start with $): {stage_name}")

        if stage_name not in allowed_stages:
            raise MongoSecurityError(f"Unknown or disallowed aggregation stage: {stage_name}")

        # Special validation for $lookup stages
        if stage_name == "$lookup":
            validate_lookup_stage(stage["$lookup"])

    return pipeline


def sanitize_regex_pattern(pattern: str) -> str:
    """
    Sanitize regex pattern to prevent ReDoS attacks.

    This is a basic implementation that prevents some common ReDoS patterns.
    For production use, consider using a more sophisticated regex validation library.

    Args:
        pattern: The regex pattern to sanitize

    Returns:
        The sanitized pattern

    Raises:
        MongoSecurityError: If the pattern is dangerous
    """
    if not isinstance(pattern, str):
        raise MongoSecurityError("Regex pattern must be a string")

    if len(pattern) > 1000:
        raise MongoSecurityError("Regex pattern is too long (max 1000 characters)")

    # Check for excessive nesting which can cause ReDoS
    open_parens = pattern.count("(")
    if open_parens > 20:
        raise MongoSecurityError("Regex pattern has too many nested groups (max 20)")

    # Check for excessive repetition operators
    dangerous_patterns = [
        r"(.+\*){3,}",  # Multiple consecutive * operators
        r"(.+\+){3,}",  # Multiple consecutive + operators
        r"\(\.\*\)\*",  # Nested (.*)*
        r"\(\.\+\)\+",  # Nested (.+)+
    ]

    for dangerous_pattern in dangerous_patterns:
        if re.search(dangerous_pattern, pattern):
            raise MongoSecurityError("Regex pattern contains potentially dangerous repetition")

    return pattern


def validate_sort_specification(sort_spec: Dict[str, int]) -> Dict[str, int]:
    """
    Validate MongoDB sort specification.

    Args:
        sort_spec: Dictionary mapping field names to sort directions (1 or -1)

    Returns:
        The validated sort specification

    Raises:
        MongoSecurityError: If the sort specification is invalid
    """
    if not isinstance(sort_spec, dict):
        raise MongoSecurityError("Sort specification must be a dictionary")

    for field, direction in sort_spec.items():
        validate_field_name(field)

        if direction not in [1, -1]:
            raise MongoSecurityError(f"Sort direction must be 1 or -1, got: {direction}")

    return sort_spec


def validate_projection(projection: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate MongoDB projection specification.

    Args:
        projection: Dictionary mapping field names to inclusion/exclusion (1 or 0)

    Returns:
        The validated projection

    Raises:
        MongoSecurityError: If the projection is invalid
    """
    if not isinstance(projection, dict):
        raise MongoSecurityError("Projection must be a dictionary")

    for field, value in projection.items():
        validate_field_name(field)

        if value not in [0, 1, True, False]:
            raise MongoSecurityError(f"Projection value must be 0, 1, True, or False, got: {value}")

    return projection
