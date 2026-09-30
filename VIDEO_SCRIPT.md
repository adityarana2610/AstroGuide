# Video Demonstration Script (5-7 Minutes)

## 1. Problem and Use Case (0:00 - 0:45)
**Speaker 1:** 
"Hello everyone! Our project is AstroGuide, an intelligent astrology assistant. The problem we identified is that while standard LLMs are great at talking about astrology, they are terrible at doing the complex astronomical math required to cast a birth chart—they frequently hallucinate planetary degrees. Conversely, traditional astrology software has the exact math but lacks conversational intelligence. 
Our use case is to bridge this gap: building an agent that uses an external Astrology API to do the hard math, and RAG to fetch interpretations, providing the user with an accurate, conversational experience."

## 2. Architecture and LangChain Components (0:45 - 2:15)
**Speaker 2:**
"Here is the architecture of AstroGuide. *(Show Architecture Diagram)*. 
We integrated **five core LangChain components**:
1. We used an **Agent** built around a ReAct loop that can decide when to use tools.
2. The agent is bound to an external **Tool**—the Astrology MCP server, which returns precise planetary JSON data.
3. We used a **VectorStoreRetriever** powered by ChromaDB. When a user asks about remedies, the agent queries this vector store to fetch data from our curated markdown files.
4. We implemented **ConversationBufferMemory** so the assistant remembers your birth details throughout the session.
5. Finally, we used custom **PromptTemplates** to enforce the persona and structure the **OutputParser**."

## 3. Live Demonstration (2:15 - 5:15)
**Speaker 3:**
"Let's jump into the live demo. 
**Test Case 1: External Tool Integration.** 
I will type: *'Generate my birth chart for Oct 26, 2001, 10:30 AM in Mumbai.'* 
As you can see in the logs, the LangChain agent decides to call the `birth_details` tool, passes the parameters, receives the JSON, and outputs a perfectly accurate planetary summary.

**Test Case 2: RAG and Memory.** 
Now I will ask: *'What gemstone should I wear to strengthen my Sun?'* 
The agent doesn't use the external tool here; instead, it uses the VectorStoreRetriever to fetch the answer from our `astrological_remedies.json` dataset. Notice how it remembered my chart from the previous question!"

## 4. Challenge Encountered (5:15 - 6:15)
**Speaker 1:**
"One major challenge we encountered was that the Astrology MCP tool is very strict—if you omit the time of birth, the API crashes. Initially, this would crash our entire LangChain pipeline.
To solve this, we implemented error handling around the tool call. If the LLM tries to call the tool without the `time` parameter, the tool throws a `ValidationError`. The agent catches this error, realizes it lacks the required input, and automatically re-prompts the user: *'I need your exact time of birth to proceed.'* This made our application highly resilient."

## 5. Limitations and Proposed Improvements (6:15 - 7:00)
**Speaker 2:**
"In terms of limitations, our vector store currently only contains data for the 9 primary planets and a few panchang rules; it lacks depth on complex multi-planet conjunctions (Yogas). Also, the LLM sometimes takes a few seconds to parse very large JSON payloads from the API.
For future improvements, we propose expanding our RAG dataset to include classical texts like BPHS, and streaming the LLM tokens to the UI to improve perceived latency. 
Thank you for watching!"
