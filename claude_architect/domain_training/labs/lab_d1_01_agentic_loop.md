# Lab D1-01: Build a Correct Agentic Loop
### Domain 1 | Task Statement 1.1 | Estimated Time: 45 minutes

---

## Objective

Build a working agentic loop from scratch that correctly handles `stop_reason`,
appends tool results to conversation history, and avoids all known anti-patterns.
Then deliberately break it three ways to understand exactly how each failure mode behaves.

---

## Prerequisites

- Python 3.10+
- `anthropic` SDK installed (`pip install anthropic`)
- `ANTHROPIC_API_KEY` set in your environment
- Basic familiarity with the Claude Messages API

---

## Setup

Create the lab file:
```
C:\Users\tsummey\projects\claude\claude_architect\labs\lab_d1_01_work.py
```

---

## Part 1: Build the Correct Loop (20 minutes)

Build an agent that helps answer questions about a fictional company's employee database.
The agent has access to two tools:

**Tool 1: `get_employee`**
- Input: `{"employee_id": "string"}`
- Returns employee name, department, salary, hire_date

**Tool 2: `get_department_stats`**
- Input: `{"department": "string"}`
- Returns headcount, average_salary, open_positions

### Step 1: Define the tools

```python
import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()

# Mock database
EMPLOYEES = {
    "E001": {"name": "Sarah Chen", "department": "Engineering", "salary": 145000, "hire_date": "2021-03-15"},
    "E002": {"name": "Marcus Webb", "department": "Sales", "salary": 98000, "hire_date": "2020-07-22"},
    "E003": {"name": "Priya Nair", "department": "Engineering", "salary": 152000, "hire_date": "2019-11-01"},
    "E004": {"name": "Tom Bradley", "department": "HR", "salary": 87000, "hire_date": "2022-01-10"},
}

DEPARTMENTS = {
    "Engineering": {"headcount": 24, "average_salary": 148000, "open_positions": 3},
    "Sales": {"headcount": 18, "average_salary": 95000, "open_positions": 5},
    "HR": {"headcount": 6, "average_salary": 88000, "open_positions": 1},
}

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""
    if tool_name == "get_employee":
        emp_id = tool_input.get("employee_id")
        employee = EMPLOYEES.get(emp_id)
        if employee:
            return json.dumps(employee)
        return json.dumps({"error": f"Employee {emp_id} not found"})

    elif tool_name == "get_department_stats":
        dept = tool_input.get("department")
        stats = DEPARTMENTS.get(dept)
        if stats:
            return json.dumps(stats)
        return json.dumps({"error": f"Department '{dept}' not found"})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})

# Tool definitions for the API
TOOLS = [
    {
        "name": "get_employee",
        "description": "Retrieves an employee's information by their employee ID. "
                       "Returns name, department, salary, and hire date. "
                       "Use this when the user asks about a specific employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID (format: E followed by 3 digits, e.g. E001)"
                }
            },
            "required": ["employee_id"]
        }
    },
    {
        "name": "get_department_stats",
        "description": "Retrieves statistics for a department including headcount, "
                       "average salary, and open positions. "
                       "Use this when the user asks about a department.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "Department name: Engineering, Sales, or HR"
                }
            },
            "required": ["department"]
        }
    }
]
```

### Step 2: Implement the correct agentic loop

```python
def run_agent(user_message: str) -> str:
    """
    Correct agentic loop implementation.
    - Checks stop_reason (not content type, not iteration count, not text parsing)
    - Appends tool results to history before every API call
    - Handles multiple tool calls in a single response
    """
    messages = [{"role": "user", "content": user_message}]
    iteration = 0
    max_iterations = 20  # Safety guard only — not primary stop mechanism

    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}")

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Iteration {iteration}] Calling Claude...")

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        print(f"  stop_reason: {response.stop_reason}")
        print(f"  content blocks: {[b.type for b in response.content]}")

        # PRIMARY stopping condition — always check stop_reason
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent response: {block.text}")
                    return block.text
            return ""

        elif response.stop_reason == "tool_use":
            # Append assistant response to history FIRST
            messages.append({"role": "assistant", "content": response.content})

            # Collect all tool results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  Tool call: {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    print(f"  Tool result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Append tool results to history
            messages.append({"role": "user", "content": tool_results})

        else:
            print(f"  Unexpected stop_reason: {response.stop_reason}")
            break

    print(f"\n[Warning] Reached max iterations ({max_iterations})")
    return "Max iterations reached"
```

### Step 3: Test it with multi-step queries

```python
if __name__ == "__main__":
    # Test 1: Single tool call
    run_agent("What department is employee E002 in?")

    # Test 2: Multi-step reasoning (requires two tool calls)
    run_agent("Is employee E001's salary above the Engineering department average?")

    # Test 3: Multiple concerns in one message
    run_agent("Tell me about employee E003 and how many open positions are in their department.")
```

### Step 4: Run it and observe

Run the script and study the output carefully:
- How many iterations does each query take?
- What does the message history look like after each iteration?
- When does `stop_reason` flip from `"tool_use"` to `"end_turn"`?

Add this debug block to print the full message history at each iteration:
```python
print(f"\n  Message history length: {len(messages)}")
for i, msg in enumerate(messages):
    role = msg["role"]
    if isinstance(msg["content"], str):
        print(f"    [{i}] {role}: {msg['content'][:80]}...")
    else:
        print(f"    [{i}] {role}: {[type(b).__name__ if not isinstance(b, dict) else b.get('type') for b in msg['content']]}")
```

---

## Part 2: Break It Three Ways (20 minutes)

Create three broken versions to understand failure modes. **Do not modify your working
version** — create a new function for each broken variant.

### Broken Version 1: Natural Language Termination Detection

```python
def run_agent_broken_v1(user_message: str) -> str:
    """
    BROKEN: Uses natural language parsing to detect completion.
    Expected failure: Will terminate early or loop forever.
    """
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        # Extract text if present
        text_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_response = block.text

        # ANTI-PATTERN: Checking text content instead of stop_reason
        if "I've found" in text_response or "The answer is" in text_response \
           or "Based on" in text_response or text_response:
            return text_response  # Terminates even if Claude is mid-reasoning!

        # Handle tool use (correct part)
        if response.stop_reason == "tool_use":
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
```

**Test it with:** `"Is employee E001's salary above the Engineering department average?"`

**Observe:** Does it complete the two-step reasoning, or does it return early?

---

### Broken Version 2: Missing Tool Results in History

```python
def run_agent_broken_v2(user_message: str) -> str:
    """
    BROKEN: Executes tools but doesn't append results to message history.
    Expected failure: Claude will repeat tool calls or hallucinate answers.
    """
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            # ANTI-PATTERN: Execute tools but DON'T append results to history
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    print(f"  Executed {block.name}: {result}")
                    # Results are executed but NEVER added to messages!
            # Claude will call the same tools again or guess the answer
```

**Test it with:** `"What is Sarah Chen's salary?"`

**Observe:** Does Claude repeat the tool call? Does it hallucinate the result?

---

### Broken Version 3: Iteration Cap as Primary Stop

```python
def run_agent_broken_v3(user_message: str) -> str:
    """
    BROKEN: Uses iteration cap as primary stopping mechanism.
    Expected failure: Cuts off complex tasks, wastes iterations on simple ones.
    """
    messages = [{"role": "user", "content": user_message}]
    MAX = 2  # Artificially low cap — primary stop mechanism

    for i in range(MAX):  # ANTI-PATTERN: loop count controls termination
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "tool_use":
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
        # No stop_reason check — just iterates MAX times and returns whatever

    # Return whatever the last response said — may be incomplete
    for block in response.content:
        if hasattr(block, "text"):
            return f"[Truncated at {MAX} iterations]: {block.text}"
    return "[No text response — task was cut off]"
```

**Test it with:** `"Is employee E001's salary above the Engineering department average?"`
(This requires 2 tool calls — will the cap of 2 iterations be enough?)

---

## Part 3: Reflection Questions (5 minutes)

Answer these in a comment block at the bottom of your file:

```python
"""
REFLECTION:

1. In Broken Version 1, what specifically caused early termination?
   Answer:

2. In Broken Version 2, what did Claude do when it didn't see tool results in history?
   Answer:

3. In Broken Version 3, what happened to the "compare salary" query with MAX=2?
   Could you fix it by just raising MAX to 10? Why or why not?
   Answer:

4. In the correct implementation, what would happen if you forgot to append the
   ASSISTANT message (with the tool call) before appending the tool result?
   Answer:

5. Why is a safety iteration cap (e.g., max_iterations=50) acceptable alongside
   stop_reason checking, but unacceptable as the PRIMARY stopping mechanism?
   Answer:
"""
```

---

## Completion Criteria

✅ Your correct implementation handles all three test queries correctly
✅ You can explain what each broken version does wrong without looking at notes
✅ You've answered all 5 reflection questions
✅ You understand exactly what the messages array looks like at each iteration

## Check Your Work

See `solutions/lab_d1_01_solution.py` for reference implementation.

---

*Next Lab: D1-02 — Multi-Agent Coordinator-Subagent System*
