# Schwarm - A Free-Form Agent Framework

**_An Opinionated Agent Framework inspired by OpenAI's swarm._**

![image](https://github.com/user-attachments/assets/2abe0238-fd79-45ba-aa50-7abd088e4ab0)

Incredibly simple yet amazingly deep, it literally wrote parts of itself.

What’s its pull? Literally manipulate everything. No state graphs that need to make sense, no hidden prompts... everything works exactly as you define it. Want to split the agent system in half after 7 rounds, reverse the flow of agents while only doing animal sounds? Yeah. No problem.

Because I’m creative, I called it *Schwarm* - the German word for *swarm*.

---

_(THIS IS AN ALPHA)_  
Seriously, this is alpha in every possible sense. It’s a playground for personal agent-based PoCs of all kinds. If you’re looking for an agent framework to perform automatic brain surgeries, you’re in the wrong place. 

If you’re looking for something that’ll blow your mind as often as it crashes... hello!  

Also, no support during alpha, but I promise the "Teachings of Schwarm" will always work.  

Edit: Since Schwarm can already implement parts of itself, the UI is shaping up pretty nicely and quickly, and I estimate beta around q1 2025.

---

## Features

- **Extend your agents with "Providers"**

  - Like with the `zep_provider` which integrates `zep` ([https://github.com/getzep/zep](https://github.com/getzep/zep)) into an agent, giving it near-infinite memory via knowledge graphs.
  - Use hundreds of LLM providers.
  - Budget tracking.
  - Token tracking.
  - Caching.
  - And so much more.

- **Don't waste your time designing your agent state machine in so much detail you end up building a normal static service by accident**

  I’ll never understand why people decide on using agents just to remove everything agentic from them with state-graphs so complex the graph itself has started to predict tokens.

  - Let agents _be_ agents.
  - Give them _dynamic_ instructions.
  - Give them _dynamic_ tools/functions.
  - Heck, make everything dynamic. Send every completion call to 50 LLMs and have another Schwarm instance rate them? No problem. Good luck doing that in LangGraph without losing your sanity.

- **Extensive logging and visualization**

  - Tell your agents to wait for your approval after every step.
  - Log everything in a way that’s actually readable.

- **Lightweight, with no memory overhead**

  - Agents aren’t memory-hogging objects idling on VRAM.
  - It’s basically one agent cosplaying as many, switching configurations dynamically.
  - *(That said, knowing my coding skills, there are probably a few million memory leaks in there.)*

- **Crazy Use Cases with A Crazy Agent Framework**

  - The light-hearted notebooks "The Teachings of Schwarm" (in `/lessons`) showcase theoretical agent concepts, everything the framework can do, and my random ramblings - all in one. Just hit play. Science definitely went too far.

---


## Quickstart

1. Install Schwarm:

   ```bash
   pip install schwarm
   ```

2. Export your OpenAI API key:

   ```bash
   export OPENAI_API_KEY=sk-xxx
   ```

3. Create your agent:

   ```python
   stephen_king_agent = Agent(name="stephen_king69", configs=[LiteLLMConfig(enable_cache=True), ZepConfig()])
   ```

   Mr. Stephen King is ready to rock! And he has his cache with him! All in one line!

   (Caching means that every message interaction will be cached, so if you send the same exact prompt to the LLM, you will receive the cached answer instead of a newly generated one. Saves money and lets you debug!)

4. How can I help you?

   Tell it what to do with dynamic instructions that can change every time it’s the agent’s turn again. Carry objects and other data from agent to agent and step to step with the help of `context_variables`.

   ```python
   def instruction_stephen_king_agent(context_variables: ContextVariables) -> str:
       """Return the instructions for the user agent."""
       instruction = """
       You are one of the best authors in the world. You are tasked to write your newest story.
       Execute "write_batch" to write something down to paper.
       Execute "remember_things" to remember things you aren’t sure about or to check if something is at odds with previously established facts.
       """
       if "book" in context_variables:
           book = context_variables["book"]
           addendum = f"\n\nYour current story has this many words right now (goal: 10,000): {len(book) / 8}"
           memory = cast(ZepProvider, ProviderManager.get_provider("zep")).get_memory()
           facts = f"\n\n\nRelevant facts about the story so far:\n{memory}"
           instruction += addendum + facts
       return instruction

   stephen_king_agent.instructions = instruction_stephen_king_agent
   ```

5. The toolbox

   Give your agent skills it wouldn’t have otherwise! Also, pass the stick to other agents by setting them in the `agent` property of the `Result` object. Just not in this example… Mr. King works alone!

   With this way of doing handoffs, you can implement every state graph you could also build with LangGraph. But this way, you keep your sanity.

   ```python
   def write_batch(context_variables: ContextVariables, text: str) -> Result:
       """Write down your story."""
       cast(ZepProvider, ProviderManager.get_provider("zep")).add_to_memory(text)
       if "book" not in context_variables:
           context_variables["book"] = ""
       context_variables["book"] += text
       return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)

   def remember_things(context_variables: ContextVariables, what_you_want_to_remember: str) -> Result:
       """If you aren’t sure about something that happened in the story, use this tool to remember it."""
       results = cast(ZepProvider, ProviderManager.get_provider("zep")).search_memory(what_you_want_to_remember)
       result = ""
       for res in results:
           result += f"\n{res.fact}"
       return Result(value=result)

   stephen_king_agent.functions = [write_batch, remember_things]
   ```

   (Based on the function name, variable names, types, and docstring, a valid OpenAI function spec JSON gets generated. So, this will only work if your model understands those. Support for other tool specs is coming!)

6. Kick off!

   ```python
   input = """
   Write a story set in the SCP universe. It should follow a group of personnel from the SCP Foundation and the adventures their work provides.
   The story should be around 10,000 words long, and should be a mix of horror and science fiction.
   Start by creating an outline for the story, and then write the first chapter.
   """

   response = Schwarm(interaction_mode='stop_and_go').quickstart(stephen_king_agent, input)
   ```

   Let your agent system loose! Don’t worry about losing all your money... this quickstart configuration will ask for your approval before performing any money-consuming task.

---

## Examples

TBD.

---

## Upcoming

- More examples and apps.
- A real documentation.
- Async / true multithreading.
- An extensive arsenal of providers.

--- 

This version stays true to your original tone but corrects errors and improves readability without losing the playful style. Let me know if you need more changes!