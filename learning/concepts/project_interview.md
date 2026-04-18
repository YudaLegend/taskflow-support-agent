# Interview questions — TaskFlow Support Agent

Questions an interviewer could ask about what's been built so far (through Day 15).
Answer each in your own words, then I'll review.

> **Scope:** covers Days 1–15 — project setup, Groq wrapper, LangGraph skeleton,
> MongoDB seeding, RAG ingestion, retrieval, eval framework, chunk-size sweeps,
> hybrid retrieval (BM25 + RRF), cross-encoder reranking, tool interface
> (Pydantic schemas + function calling), ReAct agent loop with LangGraph, and
> short-term conversation memory via checkpointers.

---

## Section 1 — Project setup & architecture

1. Give me a 60-second overview of what this project does, who the user is, and what you've built so far.
So this project focus on building a chatbot agent that helps the customers to know better a product SaaS called Taskflow that i faked building 20 markdown documents describing its features, its prices, its interactions with other apps, some FAQ. At this moment im building the tools for my agent. From this project i have built from scrath the RAG system Pipelines, i have undestood how a RAG system works and what its purpose. Then now im in the part of the AGENT tools. 

2. Why did you pick Groq over OpenAI or Anthropic? What would you change to swap providers?
So i pick up Groq cause first its a free tier allowing me called like 1000 apis calls per day. So for a first vision for my project as its a self-study project there is no need for going over OpenAI or Anthropic. And of course for what i wanted to do, with the model that Groq gives me is enough as i know the model is llama3.3 with 30B which is more tan enoubht. And also in my project i used a wrapper chat so it provides to change any model API i want withought changing entirely myy function files. So if one i wanna use another model i could easyly just change the API call. I would change to Anthroupic or a providers depending the the necessites of the product if i found that anthropic offers some SDK's that Groq it doest not offer and that function is exactly i want then i would change the providers so yeah, i would change the providers depening on the ncessites of the proiduct itself.


3. Why MongoDB (local, not Atlas)? What would break if this were a real production deployment?
First MongoDB work fine locally cause i only need to store like at most 5000 rows of raw data, and those data are sintetic so i have control of it, and for the final purpose for this project the data is the thing that i would worry the least. But we need to take care of its conditions if we were in real productions, firstly working locally you need to see the storage spaces.


4. You have a `chat()` wrapper in `agent/llm.py` instead of calling the Groq SDK directly everywhere. Why? What's the tradeoff?
Oh yeah, cause using a wrapper in agent i can change the calling by any API i want. So this way facilitates to test other models if i want to and also prevent changing other files if the Groq went down. The tradeoff is that i lose some capabilities offered by the kit but in this time i do not need cause i just need to call the LLM and nothing else.

5. Why LangGraph and not raw Python? If the current graph only has one node, was adding LangGraph overkill at this stage?
LangGraph gives me the control to customize the capabilities and tools for the agent. At this moment i just add one node for the llm calling so i will said at this stage is overkill but we nneed to look further as always, cause after i will add the tools and wire them in the Langgrapoh orchestration.



## Section 2 — RAG fundamentals

6. Walk me through what happens end-to-end when a user asks "How much does the Pro plan cost?" — from HTTP request to final answer (or, today, from CLI to final answer).
So when we do the query which is when the user asks "How much does the pro plan cost", this query will be converted into a vector of numbers which are embeddings and we will use that embedding to retrieve the top-k siumialr vectors uising the cosinnus similarity, but those are numbers right so need a more one step which reconvers those into the real documents, paragrahs. Once we get the info, we will pass it into the context of the LLM and the LLM will answer our questions uising the retrieve documents.

7. Why do we chunk docs at all? What's the tradeoff between small chunks (200 tokens) and large chunks (1000 tokens)?
We do chunks because passing the entire documents into the context of the LLM is heavy and is token wasted because most of the info is not necessary to asnwer. So instead, we divecde into the different size of chunks, those chunks it needs some experimenet to be done as we dont which size of chunks is the most suitable for our questions. SO in this project i did a experiment, using the difrent size of chunks and see if the retrieve step could get their asnwer assesing to the query. The tradeoff between 200 and 1000 is that with a small chunks we get more chunks and information is diveded into separtes chunks, and the large chunks contains more information. When we do like retireve the top-3, with small chunks maybe its not enought to asnwer our questio nadn the answer will ahave hallucionations and if with large chunks maybe we are passing more than enought there are extra info and we are occupying more tokne than necessary.


8. What is an embedding? What does the number 384 refer to in your setup?
An embedding is the way that we convert the corresponding word to a number. So the number 384 may refer a word that when we were doing the embedding step more specifically is where we do chunking and each chunk is a paragraph and those chunk is a vector of numbers and each number corrrespond to the words.
9. What does ChromaDB actually store on disk, and what does it compute at query time?
What ChromaDB stores are vector of numbers which are embeddings, what it computes is the similarity betweeen vectors. WHen we retrieve its using a simple algorith which is the k-nearesth nbeighttoutg
10. Why did you parameterize `chunk_size`, `chunk_overlap`, and `collection_name` in `ingest.py`?
Thats is the way that how we find the most suitable parameters depending on the usually queries asked to the LLM so when retrieving we will see what the optimal chunk size, chunk overlap to be set in with our purpose.

## Section 3 — Evaluation

11. You built a golden dataset of 25 Q/A pairs. Why 25 and not 5 or 500? What are the risks of each extreme?
12. Explain `hit@k` in your own words. Why did you add it even though you already had LLM-as-judge scores?
13. What's the difference between **faithfulness** and **relevancy** in your eval? Give an example of an answer that scores high on one and low on the other.
14. LLM-as-judge is noisy — you've said this yourself. What's one concrete way you could reduce that noise?
15. In Day 11, `hit@5` was 1.00 across every chunk-size config. What does that tell you? How would you fix it?

## Section 4 — Retrieval improvements (the core of Day 11)

16. What's the difference between dense retrieval and BM25, at the representation level (not just "one is neural and one isn't")?
17. Why can a bi-encoder precompute doc vectors, but a cross-encoder cannot?
18. Explain Reciprocal Rank Fusion. Why does it use ranks instead of raw scores?
19. Your hybrid retriever *regressed* compared to dense-only on this corpus. Why? What does this tell you about when hybrid helps?
20. Cross-encoder reranking is always Stage 2, never Stage 1. Why not just use the cross-encoder directly on the whole corpus?
21. If the first-stage retriever misses the correct document entirely (not in top-20), what can the reranker do? What does this imply about how you should tune `top_n`?
22. Cross-encoder scores are "higher = better" but ChromaDB distances are "lower = better." Why is this worth being paranoid about when combining retrieval systems?

## Section 5 — Experimental methodology

23. When running retrieval sweeps, you flipped `retrieval_only=True` to skip LLM calls. What was the reasoning, and when would you flip it back on?
24. There was a subtle bug in `retrieve.py` where the default argument was captured at function-def time. Explain what was wrong and why that bug would silently invalidate every experiment.
25. If I gave you twice the Groq token budget, what experiment would you run next, and why?
26. You chose not to persist the BM25 index to disk — it rebuilds in memory each run. Why is that OK for this project, and when would it stop being OK?

## Section 6 — Systems / production thinking

27. Today you have 21 docs. What changes in your architecture at 21,000 docs? At 21 million?
28. Your RAG returns a `score` for the top chunk. Could you use that as a confidence signal for a "don't-know / escalate to human" response? What's the risk?
29. Imagine the corpus is updated hourly (new help docs published). What's your reingestion strategy? What breaks if you just re-run `ingest.py` every hour?
30. What observability/logging would you add before putting this in production? Name three specific things and why.

## Section 7 — Tradeoffs & judgment

31. You have finite time. Rank these four improvements by expected ROI for a portfolio project, and justify: (a) add 50 more golden questions, (b) add cross-encoder reranking, (c) add a streaming UI, (d) add per-doc access control.
32. What's the single biggest weakness of this project right now? How would you fix it?
33. If an interviewer said "your hit@3 is already 1.00, so this project is done — why spend Day 11 on retrieval at all?", what's your defense?
34. What's one thing you'd do differently if you were starting this project from scratch today?

## Section 8 — Tools & function calling (Day 13)

35. What does "function calling" actually mean at the API level? When the LLM "calls" `get_user(email="x")`, what is it actually doing?
36. Why does each tool need its own Pydantic schema? Why not one shared schema with all possible fields as optional?
37. What's the role of the docstring on a tool function? What happens if it's vague or missing?
38. You wrapped each plain Python function with `@tool` from LangChain. Why have both — why not just write `@tool`-decorated functions in the first place?
39. Your `create_ticket` tool validates `priority` against a hardcoded set. The Pydantic schema also describes priority. Why is the runtime check still necessary?
40. What's a "structured output" and why do we care about it for tool calling specifically?
41. The `escalate_to_human` tool doesn't touch a database — it just returns a dict. Why is it still a tool? What does that say about how the LLM uses tools?
42. If the LLM hallucinates an argument value (e.g. an email that doesn't exist), where does that fail safely in your system? Where could it fail unsafely?

## Section 9 — Agent loop & LangGraph orchestration (Day 14)

43. Describe the ReAct pattern in your own words. Why is it called "ReAct"?
44. Walk me through what happens when a user asks "Show me the open tickets for jane@example.com." Name every node visited and what message gets added at each step.
45. Your router function `should_continue` doesn't decide anything — it just reads `tool_calls` from the last message. So who actually decides whether to use a tool?
46. What's the difference between your `agent` node (a function) and your `tools` node (a `ToolNode` object)? Could you have written `tools` as a function too?
47. Why do you need `recursion_limit` on `.invoke()`? What kind of bug would it catch in production?
48. You switched from `llama-3.3-70b-versatile` to `llama-4-scout` for the agent. Why? What does this teach you about choosing models for tool calling?
49. The system prompt says "ALWAYS use search_docs first" for product questions. Why isn't that enough — what could still go wrong, and how would you defend against it?
50. You moved from a custom `chat()` wrapper to `ChatGroq` + `bind_tools()`. What did you gain? What did you lose?
51. In LangGraph, a node returns a partial state update like `{"messages": [response]}`. Why a list, not a single message? What would break if you returned just `{"messages": response}`?

## Section 10 — Conversation memory (Day 15)

52. What's the difference between short-term and long-term memory for an LLM agent? Give a concrete example of each in this project.
53. Without a checkpointer, what does the agent "see" on the second invocation of a conversation? Why does this break multi-turn UX?
54. Explain `thread_id`. What happens if two users share the same `thread_id`? What happens if one user uses two different `thread_id`s?
55. You used `MemorySaver`. What are the failure modes of an in-memory checkpointer in production? What would you swap it for?
56. The checkpointer saves state after every node execution, not just at the end. Why is that useful?
57. As a conversation grows, the message list grows unbounded. What problem does this cause for the LLM? Name two strategies to handle it.
58. Tool results (e.g. a 200-row ticket dump) get saved into the checkpoint along with the user's messages. What's the risk and how would you mitigate it?
59. If a user opens a chat at 9am, walks away, and comes back at 5pm, should the agent still remember the morning's context? Defend either answer.
60. How does adding memory change the security/privacy posture of the system? What would you need to think about before launching this with real customers?

---

## How to use this file

1. Pick a section per study block.
2. Write answers inline, or in a scratchpad first, then paste them here.
3. Ask Claude to review — you'll get feedback on clarity, correctness, and
   how it lands as an interview answer (concise, specific, shows tradeoffs).
4. Add more questions as you finish Days 16+.
