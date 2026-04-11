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



