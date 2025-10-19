from typing import List, Optional, Dict, Any
from core.data_models import ColumnInsight
from .mongo_security import validate_collection_name, validate_field_name, MongoSecurityError
from .mongo_processor import execute_aggregation_pipeline, get_mongodb_connection
import os


def generate_insights(collection_name: str, field_names: Optional[List[str]] = None) -> List[ColumnInsight]:
    """
    Generate statistical insights for MongoDB collection fields

    Args:
        collection_name: Name of the collection to analyze
        field_names: Optional list of specific fields to analyze

    Returns:
        List of ColumnInsight objects with field statistics

    Raises:
        Exception: If insight generation fails
    """
    try:
        # Validate collection name
        validate_collection_name(collection_name)

        # Get database connection
        client = get_mongodb_connection()
        db_name = os.getenv("MONGODB_DATABASE", "nlq_interface")
        db = client[db_name]
        collection = db[collection_name]

        # Sample documents to determine fields if not specified
        if not field_names:
            sample_doc = collection.find_one()
            if not sample_doc:
                return []
            field_names = [key for key in sample_doc.keys() if key != '_id']
        else:
            # Validate provided field names
            for field in field_names:
                try:
                    validate_field_name(field)
                except MongoSecurityError:
                    raise Exception(f"Invalid field name: {field}")

        insights = []

        for field_name in field_names:
            # Skip _id field
            if field_name == '_id':
                continue

            # Validate field name
            try:
                validate_field_name(field_name)
            except MongoSecurityError:
                # Skip fields with invalid names
                continue

            # Get distinct count and null count using aggregation
            distinct_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "unique_values": {"$addToSet": f"${field_name}"},
                        "null_count": {
                            "$sum": {
                                "$cond": [
                                    {"$or": [
                                        {"$eq": [f"${field_name}", None]},
                                        {"$eq": [{"$type": f"${field_name}"}, "missing"]}
                                    ]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "unique_count": {"$size": "$unique_values"},
                        "null_count": 1
                    }
                }
            ]

            try:
                distinct_result = execute_aggregation_pipeline(collection_name, distinct_pipeline)
                unique_values = distinct_result[0]["unique_count"] if distinct_result else 0
                null_count = distinct_result[0]["null_count"] if distinct_result else 0
            except:
                unique_values = 0
                null_count = 0

            # Determine field type from sample document
            sample_doc = collection.find_one({field_name: {"$exists": True, "$ne": None}})
            field_type = "unknown"
            if sample_doc and field_name in sample_doc:
                field_value = sample_doc[field_name]
                python_type = type(field_value).__name__
                if python_type in ['int', 'int64']:
                    field_type = 'number'
                elif python_type in ['float', 'float64']:
                    field_type = 'double'
                elif python_type == 'bool':
                    field_type = 'boolean'
                elif python_type == 'list':
                    field_type = 'array'
                elif python_type == 'dict':
                    field_type = 'object'
                else:
                    field_type = 'string'

            insight = ColumnInsight(
                column_name=field_name,
                data_type=field_type,
                unique_values=unique_values,
                null_count=null_count
            )

            # Type-specific insights for numeric fields
            if field_type in ['number', 'double']:
                # Get min, max, avg using aggregation
                stats_pipeline = [
                    {
                        "$match": {
                            field_name: {"$exists": True, "$ne": None, "$type": ["int", "double", "long", "decimal"]}
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "min_val": {"$min": f"${field_name}"},
                            "max_val": {"$max": f"${field_name}"},
                            "avg_val": {"$avg": f"${field_name}"}
                        }
                    }
                ]

                try:
                    stats_result = execute_aggregation_pipeline(collection_name, stats_pipeline)
                    if stats_result:
                        insight.min_value = stats_result[0].get("min_val")
                        insight.max_value = stats_result[0].get("max_val")
                        insight.avg_value = stats_result[0].get("avg_val")
                except:
                    pass  # Skip if aggregation fails

            # Most common values (for all types)
            common_pipeline = [
                {
                    "$match": {
                        field_name: {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": f"${field_name}",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 5
                },
                {
                    "$project": {
                        "value": "$_id",
                        "count": 1,
                        "_id": 0
                    }
                }
            ]

            try:
                common_result = execute_aggregation_pipeline(collection_name, common_pipeline)
                if common_result:
                    insight.most_common = [
                        {"value": doc["value"], "count": doc["count"]}
                        for doc in common_result
                    ]
            except:
                pass  # Skip if aggregation fails

            insights.append(insight)

        return insights

    except Exception as e:
        raise Exception(f"Error generating insights: {str(e)}")
