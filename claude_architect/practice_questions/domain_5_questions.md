# Domain 5 Practice Questions: Context Management & Reliability
### 25 Questions | CCAF Exam Preparation

**Pass threshold: 23/25 (90%)**

---

**Q1.** After a long customer support session, the agent summarizes the conversation and loses the exact refund amount ($1,247.83) and order number (ORD-98234), replacing them with "a significant refund for a recent order." The BEST solution is:

A) Use a larger model with a longer context window to avoid summarization  
B) Extract transactional facts (amounts, dates, order IDs) into a persistent "case facts" block included in every prompt, outside the summarized history  
C) Disable conversation summarization entirely  
D) Store the conversation history in a database and retrieve it as needed  

---

**Q2.** The "lost in the middle" effect describes:

A) Tool results that get truncated when the context window is exceeded  
B) Models that reliably process information at the start and end of long inputs but may give less attention to content in the middle sections  
C) Conversations where the user's original intent is lost after many turns  
D) Subagents that lose their task context when spawned without explicit prompt injection  

---

**Q3.** A customer support agent's order lookup tool returns 40 fields including warehouse_id, packing_station_id, inventory_allocation_id, and other fields irrelevant to refund processing. After 10 order lookups, the context is dominated by these irrelevant fields. The BEST solution is:

A) Reduce the number of order lookups the agent makes  
B) Trim tool results to only the fields relevant to the current task before appending to context  
C) Use a separate summarization step after each lookup  
D) Store tool results externally and only load them when needed  

---

**Q4.** When organizing a multi-source research synthesis prompt to mitigate position effects, the BEST structure is:

A) Source materials at the beginning, key summaries at the end  
B) Key findings summary at the beginning, detailed source content in the middle, synthesis requirements at the end  
C) Source materials organized alphabetically with an index at the top  
D) All content uniformly distributed with clear section headers throughout  

---

**Q5.** A customer says: "I want to talk to a real person." Your agent has identified that the underlying issue is a simple duplicate charge it could resolve in 30 seconds. The CORRECT agent behavior is:

A) Resolve the duplicate charge first, then offer to connect with a human if needed  
B) Explain that you can resolve the issue quickly and offer to do so  
C) Escalate immediately — the customer explicitly requested a human  
D) Ask the customer to confirm they want a human before escalating  

---

**Q6.** Which is an appropriate escalation trigger?

A) The customer's sentiment score is highly negative  
B) The agent's self-reported confidence falls below 70%  
C) The customer's request involves a policy exception or gap not covered by documented policy  
D) The refund amount exceeds $100  

---

**Q7.** A customer says "I'm extremely frustrated and this is unacceptable!" but does not request a human agent. The CORRECT response is:

A) Escalate immediately — high frustration indicates the agent cannot resolve this  
B) Acknowledge the frustration and offer to resolve the issue; only escalate if the customer explicitly requests a human  
C) Ask the customer to rate their frustration 1-10 to determine escalation threshold  
D) Continue resolution without acknowledging the frustration  

---

**Q8.** A search tool returns `{"results": [], "count": 0}` regardless of whether the query found no records OR the database is unavailable. Why is this dangerous?

A) Empty arrays cause JSON parsing errors in downstream systems  
B) The coordinator treats both cases identically (no records found) and never attempts recovery for the access failure case  
C) The tool should throw an exception for access failures rather than returning a result  
D) Downstream systems cannot process zero-count results correctly  

---

**Q9.** A multi-agent research system's synthesis subagent produces a report missing key facts from a web search. The coordinator reviews it and finds one topic area underrepresented. The BEST coordinator action is:

A) Re-run the entire research pipeline from the beginning  
B) Instruct the synthesis agent to be more thorough  
C) Re-delegate a targeted search for the missing topic to the web search agent, then re-invoke synthesis with the additional findings  
D) Accept the report and note the gap in a disclaimer  

---

**Q10.** After a multi-hour codebase exploration session, Claude starts referencing "typical patterns in this type of system" instead of specific classes it analyzed earlier. This indicates:

A) The model has exhausted its knowledge of the specific codebase  
B) Context degradation — earlier detailed findings are no longer in the active context window  
C) The model is being appropriately cautious about generalizing from limited data  
D) A temperature setting that is too high, causing creative generalization  

---

**Q11.** Scratchpad files in long codebase exploration sessions are used to:

A) Store code snippets the agent generates during exploration  
B) Persist key findings across context boundaries — findings written to file survive when they scroll out of the context window  
C) Cache API responses to reduce costs during extended sessions  
D) Document the agent's reasoning process for audit purposes  

---

**Q12.** A structured error from a subagent should include `partialResults` (even if the list is empty) because:

A) Empty partialResults helps distinguish total failure from "no data found"  
B) The coordinator can use partial results to provide value even when some sources failed, annotating coverage gaps  
C) partialResults is required by the MCP protocol  
D) It reduces the coordinator's API calls by pre-populating synthesis context  

---

**Q13.** An overall extraction accuracy of 97% is reported. Stakeholders want to reduce human review. Before reducing review rates, you should:

A) Calculate the cost savings and present them to management  
B) Run 1,000 additional test extractions to confirm the 97% rate  
C) Validate accuracy by document type AND field segment — 97% overall may mask poor performance in specific categories  
D) Switch from sampling review to reviewing all low-confidence extractions only  

---

**Q14.** A synthesis agent receives findings from three subagents and produces a report. The findings included source URLs, publication dates, and specific excerpts. The final report has none of these citations. What went wrong?

A) The synthesis agent's context window was too small to include citation data  
B) Source attribution was lost during the synthesis step — the synthesis agent was not instructed to preserve claim-source mappings  
C) The report format template didn't include a citations section  
D) The subagents provided citations in a format the synthesis agent couldn't parse  

---

**Q15.** Two credible sources report different statistics: Source A says "22% office vacancy rate" and Source B says "31% vacancy rate in San Francisco specifically." How should the synthesis handle this?

A) Use the higher figure with a note that it represents the worst case  
B) Average the two figures and note there is variation  
C) Include both values with source attribution and note that they may measure different geographic scopes (national average vs. San Francisco specifically)  
D) Escalate the conflict to a human researcher to resolve before synthesizing  

---

**Q16.** The crash recovery manifest pattern for multi-agent workflows ensures:

A) Agents can communicate state directly without coordinator involvement  
B) On restart after failure, the coordinator loads agent state from the manifest and can skip already-completed agents  
C) Agent outputs are versioned and can be rolled back to earlier states  
D) The workflow always starts from the beginning on restart to ensure consistency  

---

**Q17.** An extraction confidence score of "high" for a specific field means:

A) The field value will be 100% accurate  
B) The source text explicitly and clearly stated the value without ambiguity  
C) The model is statistically confident based on pattern matching  
D) The value has been validated against a known-correct database  

---

**Q18.** Stratified random sampling of high-confidence extractions is used to:

A) Reduce the cost of human review by sampling rather than reviewing everything  
B) Detect cases where the model is incorrectly confident — errors that would be missed by reviewing only low-confidence extractions  
C) Create a representative training set for model fine-tuning  
D) Satisfy audit requirements for financial document processing  

---

**Q19.** The /compact command should be used during extended sessions when:

A) The session has been running for more than 2 hours  
B) The context window is filling up with verbose discovery output and you need room for continued exploration  
C) A task fails and you want to clear the error context before retrying  
D) You want to save the session state before making significant changes  

---

**Q20.** A customer support session has multiple issues from the same customer. The agent should decompose these into separate concerns and:

A) Handle them sequentially — complete one fully before starting the next  
B) Investigate each in parallel using shared customer context, then synthesize a unified response addressing all issues  
C) Ask the customer to file separate support tickets for each issue  
D) Focus on the highest-value issue only to maximize first-contact resolution rate  

---

**Q21.** A subagent returns this error: `{"status": "failed", "message": "search unavailable"}`. What critical information is missing?

A) The HTTP status code  
B) Failure type (transient vs. permission), whether it's retryable, what was attempted, partial results, and suggested alternatives  
C) The timestamp of the failure  
D) The subagent's ID for tracing  

---

**Q22.** Two research sources report different statistics on remote work adoption: 67% (from a 2024 study) and 45% (from a 2022 study). The synthesis agent should:

A) Use the more recent figure (67%) as the current state  
B) Include both values with their publication dates, noting the values likely reflect actual change over time rather than a discrepancy  
C) Flag the conflict for human resolution before synthesizing  
D) Average the values and note the range  

---

**Q23.** A customer gives their name as "John Smith" and the lookup tool returns 3 accounts with that name. The CORRECT agent behavior is:

A) Select the most recently active account — highest probability match  
B) Select the account with the oldest creation date — established customer  
C) Ask for additional identifying information (email, recent order number, or last 4 of payment method) before proceeding  
D) Present all three accounts to the customer and ask them to identify theirs  

---

**Q24.** Coverage annotations in synthesis outputs serve to:

A) Cite sources for legal compliance purposes  
B) Indicate which topic areas are well-supported by evidence vs. which have gaps due to source failures — letting readers calibrate trust in each section  
C) Track which subagents contributed to each section  
D) Enable automatic regeneration of under-covered sections  

---

**Q25.** Sentiment-based escalation (escalating when customer frustration exceeds a threshold) is unreliable because:

A) Sentiment analysis models are inaccurate for customer service contexts  
B) Frustration level does not correlate with case complexity — simple issues cause frustration too; complex issues that the agent can handle should be resolved, not escalated  
C) Escalation based on sentiment introduces bias against customers who express frustration  
D) Measuring frustration requires additional API calls that add latency  

---

## Answer Key

| Q | Answer | Key Concept |
|---|--------|-------------|
| 1 | B | Case facts block preserves precision outside summarized history |
| 2 | B | Middle of long context gets less model attention |
| 3 | B | Trim verbose tool outputs to relevant fields |
| 4 | B | Key summaries at start + end (high attention), details in middle |
| 5 | C | Explicit human request → immediate escalation |
| 6 | C | Policy gap/exception = escalation trigger |
| 7 | B | Frustration alone ≠ escalation; offer to resolve first |
| 8 | B | Indistinguishable failure modes prevent coordinator recovery |
| 9 | C | Targeted re-delegation + re-synthesis |
| 10 | B | Context degradation — earlier findings scrolled out |
| 11 | B | Scratchpad persists findings across context boundaries |
| 12 | B | Partial results enable partial coordinator progress |
| 13 | C | Validate by segment before reducing review |
| 14 | B | Attribution lost during synthesis — must preserve claim-source mappings |
| 15 | C | Both values with attribution + note different scopes |
| 16 | B | Manifest enables resume without rerunning completed agents |
| 17 | B | High confidence = explicitly stated in source text |
| 18 | B | Catches incorrectly-confident extractions |
| 19 | B | /compact when context filling during exploration |
| 20 | B | Parallel investigation of multiple concerns + unified response |
| 21 | B | Structured error must include failure type, retryable, attempted, alternatives |
| 22 | B | Different dates likely reflect real change — not a conflict |
| 23 | C | Multiple matches → request additional identifiers |
| 24 | B | Coverage annotations calibrate reader trust by section |
| 25 | B | Frustration ≠ complexity; wrong proxy for escalation decisions |
