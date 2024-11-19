# Schwarm

**_An Opinionated Agent Framework inspired by OpenAI's swarm._**

Incredibly simple yet amazingly deep, it literally wrote parts of it itself.

Because I'm creative I called it Schwarm. The german word for swarm.

_(THIS IS AN ALPHA - Srsly, this is an alpha in the literal sense. This is still a playground for personal agent based PoCs of all kind.
Alpha will end 2025 Q1 with the release of a web UI to Schwarm)_

## Features

- **Extend the capabilities of your agents with "Providers"**

  - A `zep_provider` integrates `zep` (https://github.com/getzep/zep) into an agent, giving it near-infinite memory with the help of knowledge graphs.
  - An `api_provider` makes your agent have its own API.
  - Use 100s of LLM providers
  - Budget tracking
  - Token tracking
  - Caching
  - And many more...

- **Don't waste your time designing your agent state machine in so much detail you end up building a normal static service by accident**

  I will never understand why people use agents just so they can remove everthing agentic from it with over-engineered graphs. Not on my watch.

  - Let your agents _be_ agents!
  - Give them _dynamic_ instructions.
  - Give them _dynamic_ functions/tools.
  - Let them figure out the rest.

- **Extensive logging and visualization**

  - Tell your agents to wait for your approval after every step.
  - Log everything that happens, presented in an actually readable and interpretable way.
  - A modern web UI is coming soon...

- **Lightweight with no overhead**
  - Agents are not real objects in your memory calling each other, and being all happy, while they are idling on your VRAM.
  - Nope. it's basically just one agent switching configurations every time it's called.

## Quickstart

1. Install Schwarm:

   ```bash
   pip install schwarm
   ```

2. Export your OpenAI API key:

   ```bash
   export OPENAI_API_KEY=sk-xxx
   ```

3. Create your agent

   ```python
   stephen_king_agent = Agent(name="mr_stephen_king", provider_config=LiteLLMConfig(enable_cache=True))
   ```

   Mr. Stephen King is ready to rock! And has his cache with them! All in one line!

   (Caching means that every message interaction will be cached, so if you would send the same exact prompt to the LLM you would receive the cached answer instead of a newly generated text. Safes money and lets you debug!)

4. How can I help you?

   Tell it what to do with dynamic instructions that can change every time it's the agent's turn again and carry objects and other data with the help of `context_variables`.

   ```python
   def instruction_stephen_king_agent(context_variables: ContextVariables) -> str:
       """Return the instructions for the Stephen King agent."""
       instruction = """
       You are one of the best authors in the world. You are tasked to write your newest story.
       Execute "write_batch" to write something down to paper.
       Execute "remember_things" to remember things you aren't sure about or to check if something is at odds with previously established facts.
       """
       if "book" in context_variables:
           book = context_variables["book"]
           addendum = f"\n\nYour current story has this many words right now (goal: 10,000): {len(book) / 8}" # highly accurate and performan word counting algorithm
           memory = zep.memory.get("user_agent", min_rating=MIN_FACT_RATING)
           facts = f"\n\nRelevant facts about the story so far:\n{memory.relevant_facts}"
           instruction += addendum + facts
       return instruction

   stephen_king_agent.instructions = instruction_stephen_king_agent
   ```

5. The toolbox

   ```python
   def write_batch(context_variables: ContextVariables, text: str) -> Result:
       """Write down your story."""
       zep.memory.add(session_id="user_agent", messages=split_text(text))
       context_variables["book"] += text
       return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)

   def remember_things(context_variables: ContextVariables, what_you_want_to_remember: str) -> Result:
       """If you aren’t sure about something that happened in the story, use this tool to remember it."""
       response = zep.memory.search_sessions(
           text=what_you_want_to_remember,
           user_id=user_id,
           search_scope="facts",
           min_fact_rating=MIN_FACT_RATING,
       )
       result = ""
       if response.results:
           for res in response.results:
               result += f"\n{res.fact}"
       return Result(value=f"{result}", context_variables=context_variables, agent=stephen_king_agent)

   stephen_king_agent.functions = [write_batch, remember_things]
   ```

   Give your agent skills it wouldn’t have otherwise! Also, pass the stick to other agents by setting them in the agent property of the Result object. Just not in this example... Mr. King works alone!
   With such a way of doing handoffs you can implement every state graph you could also build with langgraph. But you keep your sanity.

   (Based on the function name, variable names and types and the docstring, a valid OpenAI function spec json gets generated, so this will only work if your model does understand those. Support for other tool specs is coming!)

6. Kick off!

   ```python
   input = """
   Write a story set in the SCP universe. It should follow a group of personnel from the SCP Foundation and the adventures their work provides.
   The story should be around 10,000 words long, and should be a mix of horror and science fiction.
   Start by creating an outline for the story, and then write the first chapter.
   """

   response = Schwarm().quickstart(stephen_king_agent, input)
   ```

   Let your agent system loose! Don't worry about losing all your money: with this quickstart configuration, the agent system will ask for your approval before making a money-consuming task.

   (Currently all interaction happnes over the terminal. Slick web app is coming!)

## Examples

tbd.

## Upcoming

- more examples and apps
- a real documentation
- web ui
- an extensive arsenal of provider
