# Schwarm - A free-form agent framework


**_An Opinionated Agent Framework inspired by OpenAI's swarm._**

![image](https://github.com/user-attachments/assets/2abe0238-fd79-45ba-aa50-7abd088e4ab0)



Incredibly simple yet amazingly deep, it literally wrote parts of it itself.

What's its pull? Literally manipulate everything. No state-graphs that need to be sensical, no hidden prompts, everything works exactly as you define it. Want to split the agent system in half after 7 rounds, reverse the flow of agents while only doing animal sounds? Yeah. No problem.

Because I'm creative I called it Schwarm. The german word for swarm.

_(THIS IS AN ALPHA - Srsly, this is an alpha in the literal sense. This is still a playground for personal agent based PoCs of all kind. If you are looking for an agent framework doing automatic brain surgeries this is not the place you should be! If you are looking for an agent framework that will blow your mind as often as it crashes... Hello! Also no support of any kind during Alpha but I will promise the "Teaching of Schwarm" will always work)_

Edit: Due to fact that Schwarm can already implement parts of Schwarm the UI is coming along very nicely.

## Install

Get `uv` (https://docs.astral.sh/uv)

run/build/install/start ui/sync/what can't this command do:
```
uvx --with poethepoet poe miau
```

## Features

- **Extend the capabilities of your agents with "Providers"**

  - A `zep_provider` integrates `zep` (https://github.com/getzep/zep) into an agent, giving it near-infinite memory with the help of knowledge graphs.
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
  - Heck, make everything dynamic. Send ever completion call to 50 LLMs and have another instance of Schwarm rate them? No problem. Have fun doing this in langgraph without getting diverse traumata.
  - Let them figure out the rest.

- **Extensive logging and visualization**

  - Tell your agents to wait for your approval after every step.
  - Log everything that happens, presented in an actually readable and interpretable way.
  - 

- **Lightweight with no overhead**
  - Agents are not real objects in your memory calling each other, and being all happy, while they are idling on your VRAM.
  - Nope. it's basically just one agent being a master cosplayer and switching configurations every time it's called.
  - (Since I did code it it probably has like millions of mem leaks anyway)

- **Crazy Use Cases with A Crazy Agent Framework**
  - Light-hearted Notebooks "The Teachings of Schwarm" (/lessons) will introduce theoretical concepts of current agent research, will showcase everything the framework can do, and is also kind of a blog for my ramblings, and all you have to do is click some green play button! Science definitely went too far.

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
   stephen_king_agent = Agent(name="stephen_king69", configs=[LiteLLMConfig(enable_cache=True), ZepConfig()])
   ```

   Mr. Stephen King is ready to rock! And has his cache with them! All in one line!

   (Caching means that every message interaction will be cached, so if you would send the same exact prompt to the LLM you would receive the cached answer instead of a newly generated text. Safes money and lets you debug!)

4. How can I help you?

   Tell it what to do with dynamic instructions that can change every time it's the agent's turn again and carry objects and other data from agent to agent and step to step with the help of `context_variables`.

   ```python
   def instruction_stephen_king_agent(context_variables: ContextVariables) -> str:
    """Return the instructions for the user agent."""
    instruction = """
    You are one of the best authors on the world. you are tasked to write your newest story.
    Execute "write_batch" to write something down to paper.
    Execute "remember_things" to remember things you aren't sure about or to check if something is at odds with previous established facts.
    
    """
    if "book" in context_variables:
        book = context_variables["book"]
        addendum = "\n\n You current story has this many words right now (goal: 10000): " + str(len(book) / 8)

        memory = cast(ZepProvider, ProviderManager.get_provider("zep")).get_memory()
        facts = f"\n\n\nRelevant facts about the story so far:\n{memory}"
        instruction += addendum + facts
    return instruction

   stephen_king_agent.instructions = instruction_stephen_king_agent
   ```

5. The toolbox

   Give your agent skills it wouldn’t have otherwise! Also, pass the stick to other agents by setting them in the agent property of the Result object. Just not in this example... Mr. King works alone!

   With such a way of doing handoffs you can implement every state graph you could also build with langgraph. But this way you keep your sanity.

   ```python
    def write_batch(context_variables: ContextVariables, text: str) -> Result:
      """Write down your story."""
      cast(ZepProvider, ProviderManager.get_provider("zep")).add_to_memory(text)
      if "book" not in context_variables:
          context_variables["book"] = ""
      context_variables["book"] += text
      return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)


    def remember_things(context_variables: ContextVariables, what_you_want_to_remember: str) -> Result:
        """If you aren't sure about something that happened in the story, use this tool to remember it."""
        results = cast(ZepProvider, ProviderManager.get_provider("zep")).search_memory(what_you_want_to_remember)

        result = ""
        for res in results:
            result += f"\n{res.fact}"

    stephen_king_agent.functions = [write_batch, remember_things]
   ```

   (Based on the function name, variable names and types and the docstring, a valid OpenAI function spec json gets generated, so this will only work if your model does understand those. Support for other tool specs is coming!)

6. Kick off!

   ```python
   input = """
   Write a story set in the SCP universe. It should follow a group of personnel from the SCP Foundation and the adventures their work provides.
   The story should be around 10,000 words long, and should be a mix of horror and science fiction.
   Start by creating an outline for the story, and then write the first chapter.
   """

   response = Schwarm(interaction_mode='stop_and_go').quickstart(stephen_king_agent, input)
   ```

   Let your agent system loose! Don't worry about losing all your money: with this quickstart configuration, the agent system will ask for your approval before making a money-consuming task.


## Examples

tbd.

## Upcoming

- more examples and apps
- a real documentation
- async / true multithreading
- an extensive arsenal of provider
