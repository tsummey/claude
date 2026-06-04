import anthropic
from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY from .env file into the environment.
# Without this, client = anthropic.Anthropic() won't find the key.
load_dotenv()

# Create the Anthropic client. It automatically reads ANTHROPIC_API_KEY
# from the environment loaded above.
client = anthropic.Anthropic()

# stop_reason      When it fires
#-----------------------------------------------------------------------
# "end_turn"       Claude finished normally — your primary exit signal
# "tool_use"       Claude wants to call a tool — execute it and loop again
# "max_tokens"     Response hit the max_tokens limit and got cut off
# "stop_sequence"  Claude generated a custom stop sequence you defined

def execute_tool(tool_name: str, tool_input: dict):
    # Placeholder — replace with actual tool logic.
    # This is where you wire up real functionality:
    # database lookups, API calls, file reads, etc.
    pass

def run_agent(user_message: str, tools: list) -> str:

    # messages is the agent's memory. Claude has zero memory between
    # API calls — this list IS the entire conversation history.
    # Every exchange must be appended here or Claude won't know it happened.
    # Starts with just the user's request.
    messages = [{"role": "user", "content": user_message}]

    # while True runs forever until something explicitly returns or raises.
    # The loop only exits two ways:
    #   1. Normal exit  — stop_reason == "end_turn" → return
    #   2. Safety exit  — unexpected stop_reason    → raise RuntimeError
    # The loop NEVER exits based on iteration count or response text.
    while True:

        # Send the full messages history to Claude on every iteration.
        # Claude re-reads the entire history each call — this is how it
        # knows what tools it already called and what results came back.
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,   # Max length of Claude's response per call.
                               # Does NOT control how many loop iterations run.
                               # To limit iterations use a MAX_ITERATIONS safety cap.
            tools=tools,       # Tools Claude is allowed to call this session.
            messages=messages  # Full conversation history — grows each iteration.
        )

        if response.stop_reason == "end_turn":
            # Claude is genuinely done. This is the API's machine signal —
            # not text Claude wrote, but metadata the API sets specifically
            # to tell your code the task is complete.
            # Extract the text block from the response and return it.
            # This is the ONLY correct primary exit from the loop.
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        elif response.stop_reason == "tool_use":
            # Claude wants to call one or more tools before continuing.
            # Three steps must happen in order — skipping any step breaks
            # the conversation history and causes repeated tool calls or
            # hallucinated answers.

            # ✅ Step 1 — Append Claude's tool call REQUEST to messages FIRST.
            # This records that Claude asked for a tool call.
            # WHY: If you skip this, messages will contain a tool result
            # with no preceding tool call request. The conversation history
            # becomes broken and Claude will either repeat the same tool
            # call on the next iteration or hallucinate an answer because
            # it has no record of what it asked for.
            messages.append({"role": "assistant", "content": response.content})

            # ✅ Step 2 — Execute all tool calls and collect results.
            # A single response can contain MULTIPLE tool calls — collect
            # all results before appending. Never append inside this loop
            # or messages gets out of order.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,  # Links result back to the
                                                   # specific tool call request
                                                   # appended in Step 1.
                        "content": result
                    })

            # ✅ Step 3 — Append all tool results to messages SECOND.
            # WHY: Claude needs to see what the tools returned before it
            # can decide what to do next. Without this append, Claude sees
            # the same frozen messages list next iteration with no record
            # that the tools ever ran — causing infinite repeated calls.
            messages.append({"role": "user", "content": tool_results})

            # Loop continues back to the top.
            # Claude now sees the full updated history:
            #   [user message]
            #   [assistant tool call request]   ← Step 1
            #   [user tool results]             ← Step 3
            # And decides what to do next.

        else:
            # Catches max_tokens, stop_sequence, or any unexpected value.
            # Never silently ignore these — raise an error so the bug is
            # visible. Silent failure here looks like a successful response
            # but with incomplete or missing output.
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")


# Sanity check — only runs when this file is executed directly.
# Will NOT run if this file is imported by another module.
# Sends a simple message to verify the API key is valid and the
# client is connected. Expected output: a single greeting sentence.
if __name__ == "__main__":
    result = run_agent("Say hello in one sentence.", tools=[])
    print(result)