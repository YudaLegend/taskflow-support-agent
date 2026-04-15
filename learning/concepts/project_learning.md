# 01 Langgraph vs Langchain vs Deep Agents(LLM)

All of them are frameworks, and each of them has their own advantages. For example Deep Agents comes from Langchain, the documentation says that is a battery charged of langchain agents, means that those agents it already has the default modules for working. (Do not know what are those modules and what it diffeers)

Then Langchain is used to built agents when we wanna customize our own agents and built other capabilities.
Finally Langgrahph is a low-level agent Framework, this is used for a more determinitisc agent workflows and heavy customizations.

# 02 temperature, System prompts (LLM)
When the temperature of the model is set to 0, the model always pick the most likenly nex word, like if you asnwer always the same question it will return alwasy the same answer.
When is set lik 0.7, means that we want some randomness, this is good for creative writing, openmind ideas, brainstorming...
When is set to 1.5+, it is chaotic, terrible for facts.


First i ask what is a RAG, the model answered me

" RAG (Red, Amber, Green) system is a simple..."
my intention is to get asnwer about Retrieval Augmented Generation so this is a pro word from the field of ML/AI, then trying different prompts like giving them a role starting with "You are an AI/ML expert assistant ..." with this start it will get answers related with this field.

We also have the max of tokens produced by the llm, we can limited.

Short answers / classifications: 128-256
Normal conversational replies: 512-1024
Long-form (essays, summaries): 2048-4096

# 03 Langgraph (LLM)

When we are calling the llm by the API we are just doint one call at a time, so we are getting one-shot asnwer, but with LangGraph we can model the process of the Agent with LLM as a Graph. In Langgraph we got node which represents a python function, the arrow is and edge andd the flowing trought is the state. (START,END,LLM node,Tools)


# 04 ChromaDB(RAG)

ChromaDB is a vector database. Unlike the databases we usually see such as MongoDB or PostgreSQL, this kind of database is specially designed to store and search vectors (lists of numbers). This is a key component of RAG: documents are split into chunks (paragraphs or sections, roughly 500 characters each), and each chunk is converted into a single vector that represents its meaning — this process is called embedding. When we ask the LLM "How much is Pro?", the question is also embedded into a vector, and ChromaDB finds the chunks whose vectors are most similar. So literally, it's a database that stores vectors and finds similar ones fast.

We chose ChromaDB because it's free, open source, and runs locally with zero configuration. Since we only have ~200 chunks, it handles our needs easily. In production with larger datasets, you'd typically switch to a cloud-hosted vector database like Pinecone, Qdrant, or Weaviate.

# 05 Chunking (RAG)
Chunking is how you split documents into smaller pieces before embedding them. The quality of your chunks directly affects retrieval quality — good chunks contain self-contained information, bad chunks split ideas across boundaries.

Three parameters matter: chunk size (~500 chars is a common starting point), overlap (shared text between consecutive chunks to avoid cutting sentences), and splitting strategy (by character count, by headers, by meaning).

The most similar vector to a query doesn't always contain the answer — embeddings capture topic similarity, not answer relevance. All pricing-related chunks look similar to a pricing question, even if only one has the actual price.

Ways to improve retrieval:
Increase k (return more chunks, let the LLM pick the right one)
Better chunking strategy (e.g., split on ## headings so each chunk is a complete section)
Hybrid search (combine vector search with keyword search)
Reranking (retrieve many, then use a second model to reorder by relevance — more accurate but slower and costlier)


# 06 The simplest Rag Strategy (RAG)
When we do a query to llm, the agent is gonna go trought RAG and retrieve k chunks, then we gonna built the prompt like:
User asks: "How much is Pro?"
        │
        ▼
  ┌──────────┐
  │ Retrieve  │  → gets 5 chunks from ChromaDB
  └────┬─────┘
       │
       ▼
  ┌──────────────────────────────────────────┐
  │ Build prompt:                             │
  │                                           │
  │ SYSTEM: You are TaskFlow support.         │
  │ Use ONLY the context below to answer.     │
  │                                           │
  │ CONTEXT:                                  │
  │ [Source: pricing-plans.md]                │
  │ Pro is $12/user/month billed annually...  │
  │                                           │
  │ [Source: faq-general.md]                  │
  │ We offer 20% off for annual billing...    │
  │                                           │
  │ USER: How much is Pro?                    │
  └────┬─────────────────────────────────────┘
       │
       ▼
  ┌──────────┐
  │   LLM    │  → reads context, generates answer
  └────┬─────┘
       │
       ▼
  "Pro costs $12/user/month (billed annually)
   or $15/month. [Source: pricing-plans.md]"

RAG techinique is efficient to avoid the halucionation generated by the LLM. So in the system prompt we gonna make the llm onlyu answer with the provided context.

So here we got 3 concepts:
the Prompt template
Grounding: tell the LLM use the response with the actual ddata rather than its training knowdledge
Hallucionations.

# 07 The Eval (RAG)
I did a jsonl file for evaluation the faith and rel of the RAG system. But there is a interesting thing that in the RAG_SYSTEM_PROMT i put that always add the source where your answer come from and answer "i dont know" if you dont really know the asnwer so stop inventing allucinations but if it doest not know then there would not be the source but in this case:
{
    "question": "I need to speak with a human agent right now.",
    "expected": "I don't have enough information to answer that directly. Would you like me to connect you with a human agent?",
    "actual": "I don't have enough information to answer your question. Would you like me to connect you with a human agent? [Source: 00-product-brief.md]",
    "faithfulness": {
      "score": 5,
      "reason": "The answer only contains information that is supported by the context, specifically the mention of a human agent in the Enterprise section's custom pricing contact sales and the priority email support in the pricing-plans.md section."
    },
    "relevancy": {
      "score": 4,
      "reason": "The answer partially addresses the user's request by offering to connect them with a human agent, but it doesn't immediately provide the desired connection."
    }
  },

Here we got like 2 things: First the llm add the source of 00-products-brief which is not correct, solution to that is change the RAG_SYSTEM_PROMPT add like if you dont know the answer do not add th soucre. The hallucionaton is happening to the judge LLM in this phrase "specifically the mention of a human agent in the Enterprise section's custom pricing contact sales and the priority email support in the pricing-plans.md section."  But there is no human agent, it imagine one.

And the same happenns to the relevancy judge, it says " partially addresses the user's request by offering to connect them with a human agent" But your whole point was that the agent can't connect a human — that's a tool the agent doesn't have yet. Deflecting to "would you like me to connect you" is the correct behavior, not a partial one.


# 08 Retrieve and Retrieve hybrid

The normal retrieve is a process of how to manage the query and get the most similar chunks once the query is embeeded in our database. The process is the following, we embeed the query in our database and once we got the meaning vector of the query we can use the cosine similarity in order to find the most k-nearest chunk vector.

query ──► embedding ──► ChromaDB ANN search ──► top-k chunks


With Retrieve hybrid we are using 2 tehcniques one is the same as the before using embeedings and the other is the older technique BM25 which uses the TF-IDF algorith that counts words and weights them rarity. So dense(the embedding) captures meaning,  while BM25 matches keywords.
Finally we use the RRF fuses by rank position to get the top-k chunks. The scores of the two techinques are not comparable so we need to normalize them and keep on the ranks.







