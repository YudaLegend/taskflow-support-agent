# 01 Langgraph vs Langchain vs Deep Agents

All of them are frameworks, and each of them has their own advantages. For example Deep Agents comes from Langchain, the documentation says that is a battery charged of langchain agents, means that those agents it already has the default modules for working. (Do not know what are those modules and what it diffeers)

Then Langchain is used to built agents when we wanna customize our own agents and built other capabilities.
Finally Langgrahph is a low-level agent Framework, this is used for a more determinitisc agent workflows and heavy customizations.

# 02 temperature, System prompts
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

# 03 Langgraph

When we are calling the llm by the API we are just doint one call at a time, so we are getting one-shot asnwer, but with LangGraph we can model the process of the Agent with LLM as a Graph. In Langgraph we got node which represents a python function, the arrow is and edge andd the flowing trought is the state. (START,END,LLM node,Tools)


# 04 ChromaDB

ChromaDB is a vector database. Unlike the databases we usually see such as MongoDB or PostgreSQL, this kind of database is specially designed to store and search vectors (lists of numbers). This is a key component of RAG: documents are split into chunks (paragraphs or sections, roughly 500 characters each), and each chunk is converted into a single vector that represents its meaning — this process is called embedding. When we ask the LLM "How much is Pro?", the question is also embedded into a vector, and ChromaDB finds the chunks whose vectors are most similar. So literally, it's a database that stores vectors and finds similar ones fast.

We chose ChromaDB because it's free, open source, and runs locally with zero configuration. Since we only have ~200 chunks, it handles our needs easily. In production with larger datasets, you'd typically switch to a cloud-hosted vector database like Pinecone, Qdrant, or Weaviate.

# 05 Chunking
Chunking is how you split documents into smaller pieces before embedding them. The quality of your chunks directly affects retrieval quality — good chunks contain self-contained information, bad chunks split ideas across boundaries.

Three parameters matter: chunk size (~500 chars is a common starting point), overlap (shared text between consecutive chunks to avoid cutting sentences), and splitting strategy (by character count, by headers, by meaning).

The most similar vector to a query doesn't always contain the answer — embeddings capture topic similarity, not answer relevance. All pricing-related chunks look similar to a pricing question, even if only one has the actual price.

Ways to improve retrieval:
Increase k (return more chunks, let the LLM pick the right one)
Better chunking strategy (e.g., split on ## headings so each chunk is a complete section)
Hybrid search (combine vector search with keyword search)
Reranking (retrieve many, then use a second model to reorder by relevance — more accurate but slower and costlier)



