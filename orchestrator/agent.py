from orchestrator.core.tracer import ExecutionTracer
from orchestrator.llm.base import LLMClient
from orchestrator.core.tool import TOOL_REGISTRY


class Agent:
    def __init__(self, tools: list, tracer: ExecutionTracer, client: LLMClient):
        self.tools = tools
        self.tracer = tracer
        self.client = client

    def run(self, task: str):
        print(f"Agent is running task: {task}")
        tools_str = ""
        for tool_func in self.tools:
            tool_name = tool_func.__name__
            if tool_name in TOOL_REGISTRY:
                contract = TOOL_REGISTRY[tool_name]['contract']
                tools_str += f"Tool Name: {tool_name}\n"
                tools_str += f"Tool {tool_name} Inputs: {contract['inputs']}\n"
                tools_str += f"Tool {tool_name} Outputs: {contract['outputs']}\n"
                tools_str += f"Tool {tool_name} Side Effects: {contract['side_effects']}\n\n"

        system_prompt = """
        You are a helpful assistant designed to respond with a JSON object.
        Your goal is to select the single best tool to fulfill the user's request and determine the arguments for it.
        You must respond with a single, valid JSON object containing two keys: 'tool_name' and 'arguments'.
        Do not add any other text, explanations, or markdown formatting.
        """
        user_prompt = f"""
        Here are the available tools:
        ---
        {tools_str}
        ---
        User's request: "{task}"
        """
        llm_response = self.client.predict(system_prompt, user_prompt)
        print(f"LLM Response: {llm_response}")
        import json

        try:
         json_start = llm_response.find('{')
         json_end = llm_response.rfind('}') + 1
         clean_json_str = llm_response[json_start:json_end]
   
         choice = json.loads(clean_json_str)
         tool_name = choice['tool_name']
         arguments = choice['arguments']
         print(f"LLM chose tool: {tool_name} with arguments: {arguments}")
   
         tool_map = {func.__name__: func for func in self.tools}
   
         if tool_name in tool_map:
             tool_function = tool_map[tool_name]
   
             print(f"--- Executing tool: {tool_name} via tracer ---")
             result = self.tracer.trace_and_execute(tool_function, **arguments)
   
             print(f"--- Tool execution finished. Result: {result} ---")
             return result
         else:
             print(f"Error: LLM chose a tool '{tool_name}' that is not available.")
             return None
   
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error processing LLM response: {e}")
            print(f"Raw LLM response was:\n---\n{llm_response}\n---")
            return None