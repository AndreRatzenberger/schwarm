
### Example 

```python
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import litellm
from enum import Enum
import argparse
import shlex

class ToolParameter:
    def __init__(
        self,
        flag: str,
        help: str,
        required: bool = True,
        choices: List[str] = None
    ):
        self.flag = flag
        self.help = help
        self.required = required
        self.choices = choices

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        function: Callable
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

class Commandify:
    def __init__(self, model="gpt-4"):
        self.tools: Dict[str, Tool] = {}
        self.model = model
        
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        
    def _generate_tool_prompt(self) -> str:
        """Generate prompt describing all available tools"""
        prompt = "Available tools:\n\n"
        for name, tool in self.tools.items():
            prompt += f"## {name}\n"
            prompt += f"Description: {tool.description}\n"
            prompt += "Parameters:\n"
            for param in tool.parameters:
                required = "(required)" if param.required else "(optional)"
                choices = f" Choices: {param.choices}" if param.choices else ""
                prompt += f"- {param.flag}: {param.help} {required}{choices}\n"
            prompt += "\n"
        return prompt

    def _generate_selection_prompt(self, user_query: str) -> str:
        """Generate prompt for tool selection"""
        tools_prompt = self._generate_tool_prompt()
        return f"""Based on the following tools and the user's query, select the most appropriate tool and provide its name.
Do not provide any explanation, just output the tool name.

{tools_prompt}

User query: {user_query}

Selected tool:"""

    def _generate_parameter_prompt(self, tool_name: str, user_query: str) -> str:
        """Generate prompt for parameter generation"""
        tool = self.tools[tool_name]
        return f"""Given the following tool and user query, generate the appropriate CLI command.
Use only the available parameters and follow the CLI format exactly.

Tool: {tool.name}
Description: {tool.description}
Parameters:
{chr(10).join(f'- {p.flag}: {p.help}' + (f' (choices: {p.choices})' if p.choices else '') for p in tool.parameters)}

User query: {user_query}

Generate ONLY the CLI command without any explanation or additional text:"""

    async def process_query(self, user_query: str, max_retries: int = 3) -> Optional[str]:
        """Process a user query through the entire pipeline"""
        
        # Step 2: Tool Selection
        selection_prompt = self._generate_selection_prompt(user_query)
        tool_name = await self._get_llm_response(selection_prompt)
        tool_name = tool_name.strip()
        
        if tool_name not in self.tools:
            return f"Error: Selected tool '{tool_name}' is not available"
            
        # Step 3: Parameter Generation
        parameter_prompt = self._generate_parameter_prompt(tool_name, user_query)
        
        for attempt in range(max_retries):
            command = await self._get_llm_response(parameter_prompt)
            command = command.strip()
            
            # Step 4: Validation
            validation_result = self._validate_command(command)
            if validation_result == "valid":
                # Step 5: Execution
                return self._execute_command(command)
            elif attempt < max_retries - 1:
                # Retry with feedback
                parameter_prompt += f"\n\nPrevious attempt was invalid: {validation_result}\nPlease try again:"
            else:
                return f"Error: Failed to generate valid command after {max_retries} attempts"

    async def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM"""
        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=100
        )
        return response.choices[0].message.content

    def _validate_command(self, command: str) -> str:
        """Validate a generated command"""
        try:
            parts = shlex.split(command)
            if not parts:
                return "empty command"
                
            tool_name = parts[0]
            if tool_name not in self.tools:
                return f"unknown tool '{tool_name}'"
                
            tool = self.tools[tool_name]
            parser = argparse.ArgumentParser()
            
            for param in tool.parameters:
                kwargs = {
                    "help": param.help,
                    "required": param.required,
                }
                if param.choices:
                    kwargs["choices"] = param.choices
                parser.add_argument(param.flag, **kwargs)
                
            parser.parse_args(parts[1:])
            return "valid"
            
        except Exception as e:
            return str(e)

    def _execute_command(self, command: str) -> str:
        """Execute a validated command"""
        parts = shlex.split(command)
        tool_name = parts[0]
        tool = self.tools[tool_name]
        
        parser = argparse.ArgumentParser()
        for param in tool.parameters:
            parser.add_argument(param.flag)
            
        args = parser.parse_args(parts[1:])
        return tool.function(**vars(args))

# Example usage
async def main():
    # Create tools
    def emoji_translator(sentence: str, theme: str) -> str:
        themes = {
            "tech": "💻 🤖 ",
            "love": "❤️ 💕 ",
            "food": "🍕 🍔 "
        }
        return f"{sentence} {themes.get(theme, '❓ ')}"

    def meme_generator(top_text: str, bottom_text: str, template: str = "classic") -> str:
        return f"[{template}]\n{top_text}\n{bottom_text}"

    # Initialize Commandify
    commandify = Commandify()

    # Register tools
    commandify.register_tool(Tool(
        name="emoji-translator",
        description="Translates text to emoji-decorated text based on a theme",
        parameters=[
            ToolParameter("-s", "Sentence to translate", required=True),
            ToolParameter("--theme", "Theme for emojis", required=True, choices=["tech", "love", "food"])
        ],
        function=emoji_translator
    ))

    commandify.register_tool(Tool(
        name="meme-generator",
        description="Creates a meme with top and bottom text",
        parameters=[
            ToolParameter("-t", "Top text of the meme", required=True),
            ToolParameter("-b", "Bottom text of the meme", required=True),
            ToolParameter("--template", "Meme template to use", required=False)
        ],
        function=meme_generator
    ))

    # Test queries
    queries = [
        "I want to say I love coding with some tech emojis",
        "Make me a funny meme about Python programming",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        result = await commandify.process_query(query)
        print(f"Result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```


### benchmarking

```python

import litellm
import asyncio
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import json
import time

@dataclass
class TestResult:
    success: bool
    tokens_used: int
    latency: float
    error_message: str = None

class TestFramework:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.cli_commandify = Commandify(model=model)  # Your CLI approach
        self.function_tools = {}  # Traditional function calling
        
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], function: Callable):
        """Register a tool in both frameworks"""
        
        # Register for CLI approach
        cli_params = []
        for param_name, param_info in parameters['properties'].items():
            cli_params.append(ToolParameter(
                flag=f"--{param_name}",
                help=param_info.get('description', ''),
                required=param_name in parameters.get('required', []),
                choices=param_info.get('enum')
            ))
            
        self.cli_commandify.register_tool(Tool(
            name=name,
            description=description,
            parameters=cli_params,
            function=function
        ))
        
        # Register for traditional function calling
        self.function_tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        
    async def test_cli_approach(self, query: str) -> TestResult:
        """Test the CLI-based approach"""
        start_time = time.time()
        try:
            result = await self.cli_commandify.process_query(query)
            success = result is not None and not result.startswith("Error")
            # Note: You'll need to modify your Commandify class to track token usage
            return TestResult(
                success=success,
                tokens_used=self.cli_commandify.last_tokens_used,
                latency=time.time() - start_time,
                error_message=None if success else result
            )
        except Exception as e:
            return TestResult(
                success=False,
                tokens_used=0,
                latency=time.time() - start_time,
                error_message=str(e)
            )
            
    async def test_function_calling(self, query: str) -> TestResult:
        """Test the traditional function calling approach"""
        start_time = time.time()
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                functions=list(self.function_tools.values()),
                function_call="auto"
            )
            
            # Extract function call
            message = response.choices[0].message
            if not hasattr(message, 'function_call'):
                return TestResult(
                    success=False,
                    tokens_used=response.usage.total_tokens,
                    latency=time.time() - start_time,
                    error_message="No function called"
                )
                
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            
            # Execute function
            if function_name not in self.function_tools:
                return TestResult(
                    success=False,
                    tokens_used=response.usage.total_tokens,
                    latency=time.time() - start_time,
                    error_message=f"Unknown function {function_name}"
                )
                
            return TestResult(
                success=True,
                tokens_used=response.usage.total_tokens,
                latency=time.time() - start_time
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                tokens_used=0,
                latency=time.time() - start_time,
                error_message=str(e)
            )

async def main():
    # Initialize test framework
    framework = TestFramework()
    
    # Define example tools
    def emoji_translator(sentence: str, theme: str) -> str:
        themes = {
            "tech": "💻 🤖",
            "love": "❤️ 💕",
            "food": "🍕 🍔"
        }
        return f"{sentence} {themes.get(theme, '❓')}"
    
    # Register tool in both frameworks
    framework.register_tool(
        name="emoji-translator",
        description="Translates text to emoji-decorated text based on a theme",
        parameters={
            "type": "object",
            "properties": {
                "sentence": {
                    "type": "string",
                    "description": "Sentence to translate"
                },
                "theme": {
                    "type": "string",
                    "description": "Theme for emojis",
                    "enum": ["tech", "love", "food"]
                }
            },
            "required": ["sentence", "theme"]
        },
        function=emoji_translator
    )
    
    # Test cases
    test_cases = [
        "I want to say I love coding with some tech emojis",
        "Make this food related: I'm hungry",
        "Invalid request that shouldn't work",
        "Tech theme: Hello World",
    ]
    
    # Run tests
    for query in test_cases:
        print(f"\nTesting query: {query}")
        
        # Test CLI approach
        cli_result = await framework.test_cli_approach(query)
        print(f"CLI Approach:")
        print(f"  Success: {cli_result.success}")
        print(f"  Tokens: {cli_result.tokens_used}")
        print(f"  Latency: {cli_result.latency:.2f}s")
        if cli_result.error_message:
            print(f"  Error: {cli_result.error_message}")
            
        # Test function calling
        func_result = await framework.test_function_calling(query)
        print(f"Function Calling:")
        print(f"  Success: {func_result.success}")
        print(f"  Tokens: {func_result.tokens_used}")
        print(f"  Latency: {func_result.latency:.2f}s")
        if func_result.error_message:
            print(f"  Error: {func_result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())

```


### benchmark ui

```typescript
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// Sample data structure - would come from your test framework
const sampleData = {
  testCases: [
    {
      query: "I want to say I love coding with some tech emojis",
      cli: {
        success: true,
        tokens: 145,
        latency: 0.8,
        error: null
      },
      functionCall: {
        success: true,
        tokens: 178,
        latency: 0.9,
        error: null
      }
    },
    {
      query: "Make this food related: I'm hungry",
      cli: {
        success: true,
        tokens: 132,
        latency: 0.7,
        error: null
      },
      functionCall: {
        success: false,
        tokens: 156,
        latency: 0.85,
        error: "Invalid theme specified"
      }
    },
    {
      query: "Invalid request that shouldn't work",
      cli: {
        success: false,
        tokens: 120,
        latency: 0.6,
        error: "Could not determine appropriate tool"
      },
      functionCall: {
        success: false,
        tokens: 145,
        latency: 0.75,
        error: "No matching function found"
      }
    }
  ]
};

const ToolComparisonDashboard = () => {
  const [selectedMetric, setSelectedMetric] = useState('success');

  // Compute aggregate metrics
  const aggregateMetrics = {
    success: {
      cli: sampleData.testCases.filter(tc => tc.cli.success).length / sampleData.testCases.length * 100,
      functionCall: sampleData.testCases.filter(tc => tc.functionCall.success).length / sampleData.testCases.length * 100
    },
    avgTokens: {
      cli: sampleData.testCases.reduce((sum, tc) => sum + tc.cli.tokens, 0) / sampleData.testCases.length,
      functionCall: sampleData.testCases.reduce((sum, tc) => sum + tc.functionCall.tokens, 0) / sampleData.testCases.length
    },
    avgLatency: {
      cli: sampleData.testCases.reduce((sum, tc) => sum + tc.cli.latency, 0) / sampleData.testCases.length,
      functionCall: sampleData.testCases.reduce((sum, tc) => sum + tc.functionCall.latency, 0) / sampleData.testCases.length
    }
  };

  // Transform data for charts
  const chartData = [
    {
      metric: 'Success Rate (%)',
      CLI: aggregateMetrics.success.cli,
      'Function Call': aggregateMetrics.success.functionCall
    },
    {
      metric: 'Avg Tokens Used',
      CLI: aggregateMetrics.avgTokens.cli,
      'Function Call': aggregateMetrics.avgTokens.functionCall
    },
    {
      metric: 'Avg Latency (s)',
      CLI: aggregateMetrics.avgLatency.cli,
      'Function Call': aggregateMetrics.avgLatency.functionCall
    }
  ];

  // Individual test case results for detailed view
  const testCaseData = sampleData.testCases.map((tc, idx) => ({
    name: `Test ${idx + 1}`,
    'CLI Tokens': tc.cli.tokens,
    'Function Call Tokens': tc.functionCall.tokens,
    'CLI Latency': tc.cli.latency,
    'Function Call Latency': tc.functionCall.latency
  }));

  return (
    <div className="space-y-8 p-4">
      {/* Overview Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Tool Calling Comparison Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="metric" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="CLI" fill="#8884d8" />
                <Bar dataKey="Function Call" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Test Case Results */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Test Case Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={testCaseData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="CLI Tokens" fill="#8884d8" />
                <Bar dataKey="Function Call Tokens" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Error Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Error Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sampleData.testCases.map((tc, idx) => (
              <div key={idx} className="border p-4 rounded">
                <p className="font-medium">Query: {tc.query}</p>
                <div className="grid grid-cols-2 gap-4 mt-2">
                  <div>
                    <p className="font-medium">CLI</p>
                    <p className={tc.cli.success ? "text-green-600" : "text-red-600"}>
                      {tc.cli.success ? "Success" : `Failed: ${tc.cli.error}`}
                    </p>
                  </div>
                  <div>
                    <p className="font-medium">Function Call</p>
                    <p className={tc.functionCall.success ? "text-green-600" : "text-red-600"}>
                      {tc.functionCall.success ? "Success" : `Failed: ${tc.functionCall.error}`}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ToolComparisonDashboard;
```

### benchmark
```python
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BenchmarkCase:
    id: str
    question: str
    available_functions: List[Dict[str, Any]]
    ground_truth: str
    execution_result_type: List[str]

@dataclass
class TestResult:
    case_id: str
    approach: str  # 'cli' or 'function_call'
    success: bool
    tokens_used: int
    latency: float
    generated_code: str
    error: Optional[str] = None

class Benchmark:
    def __init__(self, cli_framework, function_call_framework):
        self.cli_framework = cli_framework
        self.function_call_framework = function_call_framework
        self.test_cases: List[BenchmarkCase] = []
        self.results: List[TestResult] = []
        
    def load_test_cases(self, jsonl_file: str):
        """Load test cases from a JSONL file"""
        self.test_cases = []
        with open(jsonl_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                # Extract the first (and usually only) question
                question = data['question'][0][0]['content']
                self.test_cases.append(BenchmarkCase(
                    id=data['id'],
                    question=question,
                    available_functions=data['function'],
                    ground_truth=data['ground_truth'][0],
                    execution_result_type=data['execution_result_type']
                ))
                
    async def run_benchmarks(self):
        """Run all test cases through both approaches"""
        for case in self.test_cases:
            # Test CLI approach
            cli_result = await self._run_cli_test(case)
            self.results.append(cli_result)
            
            # Test function calling approach
            fc_result = await self._run_function_call_test(case)
            self.results.append(fc_result)
            
    async def _run_cli_test(self, case: BenchmarkCase) -> TestResult:
        """Run a single test case through the CLI approach"""
        start_time = datetime.now()
        try:
            result = await self.cli_framework.process_query(case.question)
            end_time = datetime.now()
            success = self._validate_result(result, case.ground_truth)
            return TestResult(
                case_id=case.id,
                approach='cli',
                success=success,
                tokens_used=self.cli_framework.last_tokens_used,
                latency=(end_time - start_time).total_seconds(),
                generated_code=result
            )
        except Exception as e:
            end_time = datetime.now()
            return TestResult(
                case_id=case.id,
                approach='cli',
                success=False,
                tokens_used=0,
                latency=(end_time - start_time).total_seconds(),
                generated_code="",
                error=str(e)
            )
            
    async def _run_function_call_test(self, case: BenchmarkCase) -> TestResult:
        """Run a single test case through the function calling approach"""
        start_time = datetime.now()
        try:
            result = await self.function_call_framework.process_query(
                case.question,
                case.available_functions
            )
            end_time = datetime.now()
            success = self._validate_result(result, case.ground_truth)
            return TestResult(
                case_id=case.id,
                approach='function_call',
                success=success,
                tokens_used=self.function_call_framework.last_tokens_used,
                latency=(end_time - start_time).total_seconds(),
                generated_code=result
            )
        except Exception as e:
            end_time = datetime.now()
            return TestResult(
                case_id=case.id,
                approach='function_call',
                success=False,
                tokens_used=0,
                latency=(end_time - start_time).total_seconds(),
                generated_code="",
                error=str(e)
            )
            
    def _validate_result(self, result: str, ground_truth: str) -> bool:
        """Validate if the result matches the ground truth"""
        # Clean up strings for comparison
        result = result.strip().replace(" ", "")
        ground_truth = ground_truth.strip().replace(" ", "")
        return result == ground_truth
        
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate benchmark statistics"""
        cli_results = [r for r in self.results if r.approach == 'cli']
        fc_results = [r for r in self.results if r.approach == 'function_call']
        
        def calc_stats(results):
            total = len(results)
            successful = len([r for r in results if r.success])
            avg_tokens = sum(r.tokens_used for r in results) / total if total > 0 else 0
            avg_latency = sum(r.latency for r in results) / total if total > 0 else 0
            return {
                "total_cases": total,
                "successful_cases": successful,
                "success_rate": successful / total if total > 0 else 0,
                "avg_tokens": avg_tokens,
                "avg_latency": avg_latency
            }
            
        return {
            "cli": calc_stats(cli_results),
            "function_call": calc_stats(fc_results),
            "test_cases": len(self.test_cases)
        }

# Example usage
async def main():
    # Initialize your frameworks
    cli_framework = Commandify()
    function_call_framework = TraditionalFunctionCaller()
    
    # Create benchmark instance
    benchmark = Benchmark(cli_framework, function_call_framework)
    
    # Load test cases
    benchmark.load_test_cases("function_calling_benchmark.jsonl")
    
    # Run benchmarks
    await benchmark.run_benchmarks()
    
    # Get statistics
    stats = benchmark.get_statistics()
    print("\nBenchmark Results:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

```