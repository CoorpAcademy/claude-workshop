import pytest
import os
from unittest.mock import patch, MagicMock
from core.llm_processor import (
    generate_mongodb_query_with_openai,
    generate_mongodb_query_with_anthropic,
    format_schema_for_prompt,
    generate_mongodb_query
)
from core.data_models import QueryRequest


class TestLLMProcessor:
    
    @patch('core.llm_processor.OpenAI')
    def test_generate_mongodb_query_with_openai_success(self, mock_openai_class):
        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"query_type": "find", "collection": "users", "query": {"age": {"$gt": 25}}, "limit": 100}'
        mock_client.chat.completions.create.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show me users older than 25"
            schema_info = {
                'users': {
                    'count': 100,
                    'fields': {'id': {'type': 'number'}, 'name': {'type': 'string'}, 'age': {'type': 'number'}}
                }
            }

            result = generate_mongodb_query_with_openai(query_text, schema_info)

            assert result['query_type'] == 'find'
            assert result['collection'] == 'users'
            assert result['query'] == {"age": {"$gt": 25}}
            mock_client.chat.completions.create.assert_called_once()

            # Verify the API call parameters
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4o-mini'
            assert call_args[1]['temperature'] == 0.1
            assert call_args[1]['max_tokens'] == 1000
    
    @patch('core.llm_processor.OpenAI')
    def test_generate_mongodb_query_with_openai_clean_markdown(self, mock_openai_class):
        # Test MongoDB query cleanup from markdown
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"query_type": "find", "collection": "users", "query": {}, "limit": 100}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show all users"
            schema_info = {}

            result = generate_mongodb_query_with_openai(query_text, schema_info)

            assert result['query_type'] == 'find'
            assert result['collection'] == 'users'
            assert result['query'] == {}
    
    def test_generate_mongodb_query_with_openai_no_api_key(self):
        # Test error when API key is not set
        with patch.dict(os.environ, {}, clear=True):
            query_text = "Show all users"
            schema_info = {}

            with pytest.raises(Exception) as exc_info:
                generate_mongodb_query_with_openai(query_text, schema_info)

            assert "OPENAI_API_KEY environment variable not set" in str(exc_info.value)
    
    @patch('core.llm_processor.OpenAI')
    def test_generate_mongodb_query_with_openai_api_error(self, mock_openai_class):
        # Test API error handling
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show all users"
            schema_info = {}

            with pytest.raises(Exception) as exc_info:
                generate_mongodb_query_with_openai(query_text, schema_info)

            assert "Error generating MongoDB query with OpenAI" in str(exc_info.value)
    
    @patch('core.llm_processor.Anthropic')
    def test_generate_mongodb_query_with_anthropic_success(self, mock_anthropic_class):
        # Mock Anthropic client and response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content[0].text = '{"query_type": "find", "collection": "products", "query": {"price": {"$lt": 100}}, "limit": 100}'
        mock_client.messages.create.return_value = mock_response

        # Mock environment variable
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show me products under $100"
            schema_info = {
                'products': {
                    'count': 50,
                    'fields': {'id': {'type': 'number'}, 'name': {'type': 'string'}, 'price': {'type': 'number'}}
                }
            }

            result = generate_mongodb_query_with_anthropic(query_text, schema_info)

            assert result['query_type'] == 'find'
            assert result['collection'] == 'products'
            assert result['query'] == {"price": {"$lt": 100}}
            mock_client.messages.create.assert_called_once()

            # Verify the API call parameters
            call_args = mock_client.messages.create.call_args
            assert call_args[1]['model'] == 'claude-3-5-haiku-20241022'
            assert call_args[1]['temperature'] == 0.1
            assert call_args[1]['max_tokens'] == 1000
    
    @patch('core.llm_processor.Anthropic')
    def test_generate_mongodb_query_with_anthropic_clean_markdown(self, mock_anthropic_class):
        # Test MongoDB query cleanup from markdown
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content[0].text = '{"query_type": "find", "collection": "orders", "query": {}, "limit": 100}'
        mock_client.messages.create.return_value = mock_response

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show all orders"
            schema_info = {}

            result = generate_mongodb_query_with_anthropic(query_text, schema_info)

            assert result['query_type'] == 'find'
            assert result['collection'] == 'orders'

    def test_generate_mongodb_query_with_anthropic_no_api_key(self):
        # Test error when API key is not set
        with patch.dict(os.environ, {}, clear=True):
            query_text = "Show all orders"
            schema_info = {}

            with pytest.raises(Exception) as exc_info:
                generate_mongodb_query_with_anthropic(query_text, schema_info)

            assert "ANTHROPIC_API_KEY environment variable not set" in str(exc_info.value)

    @patch('core.llm_processor.Anthropic')
    def test_generate_mongodb_query_with_anthropic_api_error(self, mock_anthropic_class):
        # Test API error handling
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show all orders"
            schema_info = {}

            with pytest.raises(Exception) as exc_info:
                generate_mongodb_query_with_anthropic(query_text, schema_info)

            assert "Error generating MongoDB query with Anthropic" in str(exc_info.value)
    
    def test_format_schema_for_prompt(self):
        # Test schema formatting for LLM prompt
        schema_info = {
            'users': {
                'count': 100,
                'fields': {
                    'id': {'type': 'number', 'sample': 1},
                    'name': {'type': 'string', 'sample': 'John'},
                    'age': {'type': 'number', 'sample': 25}
                }
            },
            'products': {
                'count': 50,
                'fields': {
                    'id': {'type': 'number', 'sample': 1},
                    'name': {'type': 'string', 'sample': 'Product'},
                    'price': {'type': 'number', 'sample': 99.99}
                }
            }
        }

        result = format_schema_for_prompt(schema_info)

        assert "Collection: users" in result
        assert "Collection: products" in result
        assert "Document count: 100" in result
        assert "Document count: 50" in result
        assert "name (string)" in result
        assert "age (number)" in result
        assert "price (number)" in result

    def test_format_schema_for_prompt_empty(self):
        # Test with empty schema
        schema_info = {}

        result = format_schema_for_prompt(schema_info)

        assert result == ""
    
    @patch('core.llm_processor.generate_mongodb_query_with_openai')
    def test_generate_mongodb_query_openai_key_priority(self, mock_openai_func):
        # Test that OpenAI is used when OpenAI key exists (regardless of request preference)
        mock_openai_func.return_value = {"query_type": "find", "collection": "users", "query": {}}

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'}):
            request = QueryRequest(query="Show all users", llm_provider="anthropic")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'users'
            mock_openai_func.assert_called_once_with("Show all users", schema_info)
    
    @patch('core.llm_processor.generate_mongodb_query_with_anthropic')
    def test_generate_mongodb_query_anthropic_fallback(self, mock_anthropic_func):
        # Test that Anthropic is used when only Anthropic key exists
        mock_anthropic_func.return_value = {"query_type": "find", "collection": "products", "query": {}}

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'anthropic-key'}, clear=True):
            request = QueryRequest(query="Show all products", llm_provider="openai")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'products'
            mock_anthropic_func.assert_called_once_with("Show all products", schema_info)

    @patch('core.llm_processor.generate_mongodb_query_with_openai')
    def test_generate_mongodb_query_request_preference_openai(self, mock_openai_func):
        # Test request preference when no keys available
        mock_openai_func.return_value = {"query_type": "find", "collection": "orders", "query": {}}

        with patch.dict(os.environ, {}, clear=True):
            request = QueryRequest(query="Show all orders", llm_provider="openai")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'orders'
            mock_openai_func.assert_called_once_with("Show all orders", schema_info)

    @patch('core.llm_processor.generate_mongodb_query_with_anthropic')
    def test_generate_mongodb_query_request_preference_anthropic(self, mock_anthropic_func):
        # Test request preference when no keys available
        mock_anthropic_func.return_value = {"query_type": "find", "collection": "customers", "query": {}}

        with patch.dict(os.environ, {}, clear=True):
            request = QueryRequest(query="Show all customers", llm_provider="anthropic")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'customers'
            mock_anthropic_func.assert_called_once_with("Show all customers", schema_info)

    @patch('core.llm_processor.generate_mongodb_query_with_openai')
    def test_generate_mongodb_query_both_keys_openai_priority(self, mock_openai_func):
        # Test that OpenAI has priority when both keys exist
        mock_openai_func.return_value = {"query_type": "find", "collection": "inventory", "query": {}}

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'}):
            request = QueryRequest(query="Show inventory", llm_provider="anthropic")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'inventory'
            mock_openai_func.assert_called_once_with("Show inventory", schema_info)

    @patch('core.llm_processor.generate_mongodb_query_with_openai')
    def test_generate_mongodb_query_only_openai_key(self, mock_openai_func):
        # Test when only OpenAI key exists
        mock_openai_func.return_value = {"query_type": "find", "collection": "sales", "query": {}}

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}, clear=True):
            request = QueryRequest(query="Show sales data", llm_provider="anthropic")
            schema_info = {}

            result = generate_mongodb_query(request, schema_info)

            assert result['collection'] == 'sales'
            mock_openai_func.assert_called_once_with("Show sales data", schema_info)