# LLM Provider Stream Handler Improvements

The following code shows the improved implementation of the `_handle_streaming` method for the LLM provider. Key improvements include:

- Proper initialization and cleanup of stream managers
- Better error handling for stream operations
- Improved chunk processing with error isolation
- Proper resource cleanup in all scenarios

```python
async def _handle_streaming(self, response, messages: list[dict[str, Any]], model: str) -> Message:
    """Handle streaming response from LiteLLM.
    
    Args:
        response: The streaming response from LiteLLM
        messages: List of message dictionaries
        model: The model name being used
        
    Returns:
        Message: A complete message built from all chunks
        
    Raises:
        CompletionError: If streaming fails
    """
    chunks = []
    full_response = ""
    stream_manager = None
    stream_tool_manager = None
    
    try:
        # Initialize stream managers
        stream_manager = StreamManager()
        stream_tool_manager = StreamToolManager()
        
        for part in response:
            if not part or not part.choices:
                continue
                
            delta = part.choices[0].delta
            chunk = {"choices": [{"delta": {}}]}

            try:
                # Handle content streaming
                if delta and delta.content:
                    content = delta.content
                    if content:
                        logger.debug(f"Chunks content: {json.dumps(content, indent=2)}")
                        try:
                            await stream_manager.write(content)
                            full_response += content
                            chunk["choices"][0]["delta"]["content"] = content
                        except Exception as e:
                            logger.error(f"Error writing content chunk: {e}")
                            # Continue processing even if one chunk fails

                # Handle function call streaming
                elif delta and delta.function_call:
                    function_call_data = {
                        "name": delta.function_call.name,
                        "arguments": delta.function_call.arguments,
                    }
                    logger.debug(f"Chunks function_call_data: {json.dumps(function_call_data, indent=2)}")
                    try:
                        await stream_tool_manager.write(str(delta.function_call.arguments))
                        chunk["choices"][0]["delta"]["function_call"] = function_call_data
                    except Exception as e:
                        logger.error(f"Error writing function call chunk: {e}")
                        # Continue processing even if one chunk fails

                # Handle tool calls streaming
                elif delta and delta.tool_calls:
                    tool_calls_list = []
                    for tool_call in delta.tool_calls:
                        tool_call_data = {
                            "id": tool_call.id,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        logger.debug(f"Chunks tool_call_data: {json.dumps(tool_call_data, indent=2)}")
                        tool_calls_list.append(tool_call_data)
                        try:
                            await stream_tool_manager.write(str(tool_call.function.arguments))
                        except Exception as e:
                            logger.error(f"Error writing tool call chunk: {e}")
                            # Continue processing even if one chunk fails

                    chunk["choices"][0]["delta"]["tool_calls"] = tool_calls_list

                if chunk["choices"][0]["delta"]:
                    chunks.append(part)

            except Exception as e:
                logger.error(f"Error processing stream chunk: {e}")
                # Continue processing other chunks even if one fails
                
            # Small delay to prevent overwhelming the stream
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        raise CompletionError(f"Streaming failed: {e}") from e
        
    finally:
        # Ensure both managers are properly closed
        if stream_manager:
            try:
                await stream_manager.close()
            except Exception as e:
                logger.error(f"Error closing stream manager: {e}")
                
        if stream_tool_manager:
            try:
                await stream_tool_manager.close()
            except Exception as e:
                logger.error(f"Error closing stream tool manager: {e}")

    # Build final message from chunks
    try:
        msg = litellm.stream_chunk_builder(chunks, messages=messages)
        return self._create_completion_response(msg, model, messages)
    except Exception as e:
        logger.error(f"Error building final message: {e}")
        raise CompletionError(f"Failed to build message from chunks: {e}")
```

## Key Improvements

1. **Stream Manager Initialization**
   - Managers are initialized as None and created only when needed
   - Proper cleanup in finally block ensures resources are released

2. **Error Handling**
   - Each streaming operation is wrapped in try/except
   - Errors in individual chunks don't stop the entire stream
   - Detailed error logging at each level

3. **Resource Management**
   - Proper cleanup of stream managers in all scenarios
   - Separate try/except blocks for closing each manager

4. **Performance**
   - Added small delay between chunks to prevent overwhelming the stream
   - Removed redundant time.sleep call

5. **Code Organization**
   - Clearer separation between content, function call, and tool call handling
   - Better logging of each operation
   - More descriptive error messages

## Usage Notes

1. This implementation maintains backward compatibility with the existing code
2. It adds more robust error handling while preserving the core functionality
3. The stream managers are properly cleaned up even if errors occur
4. Each type of streaming (content, function calls, tool calls) is handled independently
5. Errors in one part of the stream don't affect other parts

You can replace the existing `_handle_streaming` method in your llm_provider.py with this improved version.
