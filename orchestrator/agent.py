import logging
import json
from orchestrator.core.tracer import ExecutionTracer
from orchestrator.llm.base import LLMClient
from orchestrator.core.tool import TOOL_REGISTRY


class Agent:
    def __init__(self, tools: list, tracer: ExecutionTracer, client: LLMClient):
        self.tools = tools
        self.tracer = tracer
        self.client = client
        self.tool_map = {func.__name__: func for func in self.tools}

    def run(self, task: str):
        return self.run_react(task, max_steps=1)

    def make_prompt(self, task: str, history: str = "") -> tuple[str, str]:
        tools_str = self.get_tools_str()

        system_prompt = """
        You are a helpful assistant that completes a task by planning and executing a sequence of tool calls.
        Your goal is to decide the single next step to achieve the user's request.
        
        You must respond with a single, valid JSON object with four keys:
        1. 'thought': A string explaining your reasoning for the chosen action.
        2. 'confidence': A float from 0.0 to 1.0 indicating your confidence in this choice.
        3. 'tool_name': The name of the tool to call.
        4. 'arguments': A dictionary of arguments for the tool.
        
        If you believe the task is complete, you must use the special tool 'finish' and provide the final answer.
        Do not add any other text, explanations, or markdown formatting.
        """

        user_prompt = f"""
        Here are the available tools:
        ---
        {tools_str}
        ---
        Here is the history of the steps executed so far:
        ---
        {history}
        ---
        Based on the history, what is the single next step to achieve the following user request?
        User's request: "{task}"
        """
        return system_prompt, user_prompt

    def get_tools_str(self) -> str:
        tools_str = ""
        for tool_func in self.tools:
            tool_name = tool_func.__name__
            if tool_name in TOOL_REGISTRY:
                contract = TOOL_REGISTRY[tool_name]["contract"]
                tools_str += f"Tool Name: {tool_name}\n"
                tools_str += f"Inputs: {contract['inputs']}\n\n"
        tools_str += "Tool Name: finish\n"
        tools_str += (
            "Inputs: {{'answer': 'The final answer to the user's request'}}\n\n"
        )
        return tools_str

    def run_react(self, task: str, max_steps: int = 10):
        logging.info(f"Agent is running task with ReAct loop: {task}")

        successful_steps = []
        history = "No steps taken yet."

        for i in range(max_steps):
            logging.info(f"\n--- Step {i + 1} ---")

            system_prompt, user_prompt = self.make_prompt(task, history)
            llm_response = self.client.predict(system_prompt, user_prompt)
            logging.debug(f"LLM Response: {llm_response}")

            try:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                clean_json_str = llm_response[json_start:json_end]
                choice = json.loads(clean_json_str)

                thought = choice.get("thought", "N/A")
                confidence = choice.get("confidence", 1.0)
                tool_name = choice["tool_name"]
                arguments = choice["arguments"]
                logging.info(f"LLM chose tool: {tool_name} with arguments: {arguments}")
                logging.debug(f"LLM thought: {thought}")

                if tool_name == "finish":
                    logging.info(
                        f"--- Workflow finished. Final Answer: {arguments.get('answer')} ---"
                    )
                    return {
                        "status": "Workflow succeeded.",
                        "final_answer": arguments.get("answer"),
                    }

                if tool_name in self.tool_map:
                    tool_function = self.tool_map[tool_name]

                    self.tracer.set_trace_context(
                        reasoning=thought, confidence=confidence
                    )

                    result = self.tracer.trace_and_execute(tool_function, **arguments)

                    successful_steps.append(
                        {"tool_name": tool_name, "arguments": arguments}
                    )
                    history += f"\nStep {i + 1}: Executed tool '{tool_name}'. Observation: {result}"
                    logging.info(f"--- Tool execution finished. Result: {result} ---")
                else:
                    raise KeyError(
                        f"LLM chose a tool '{tool_name}' that is not available."
                    )

            except Exception as e:
                logging.error(f"--- Step {i + 1} FAILED: {e} ---")
                logging.warning("--- INITIATING ROLLBACK ---")

                for step in reversed(successful_steps):
                    completed_tool_name = step["tool_name"]
                    logging.info(f"Checking for rollback for: {completed_tool_name}")

                    contract = TOOL_REGISTRY[completed_tool_name]["contract"]
                    compensating_tool_name = contract.get("compensating_tool")

                    if (
                        compensating_tool_name
                        and compensating_tool_name in self.tool_map
                    ):
                        logging.info(
                            f"Found compensating tool: {compensating_tool_name}. Running it now."
                        )
                        compensating_tool_func = self.tool_map[compensating_tool_name]
                        self.tracer.set_trace_context(
                            "Executing compensating tool for failed workflow.", 1.0
                        )
                        self.tracer.trace_and_execute(
                            compensating_tool_func, **step["arguments"]
                        )
                    else:
                        logging.warning(
                            f"No compensating tool found for {completed_tool_name}."
                        )

                logging.info("--- Rollback complete. Halting workflow. ---")
                return {"status": "Workflow failed and was rolled back."}

        logging.warning("--- Workflow finished due to max steps reached. ---")
        return {"status": "Workflow finished due to max steps."}
