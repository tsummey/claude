import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# stop_reason      When it fires
#-----------------------------------------------------------------------
# "end_turn"       Claude finished normally — your primary exit signal
# "tool_use"       Claude wants to call a tool — execute it and loop again
# "max_tokens"     Response hit the max_tokens limit and got cut off
# "stop_sequence"  Claude generated a custom stop sequence you defined

def execute_tool(tool_name: str, tool_input: dict):
    # Placeholder — replace with your actual tool logic
    pass

def run_agent(user_message: str, tools: list) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")

# Sanity check — verify API connection
if __name__ == "__main__":
    result = run_agent("Say hello in one sentence.", tools=[])
    print(result)