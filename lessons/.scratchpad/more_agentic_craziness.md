
## Wild Agent Tricks That Actually Work

### The Shape-Shifting Agent
```python
def chameleon_instructions(context: ContextVariables) -> str:
    personas = {
        "pirate": "Ye be a salty sea dog, specializin' in naval warfare!",
        "scientist": "You are a meticulous researcher with 3 PhDs.",
        "chef": "You are Gordon Ramsay's angrier twin."
    }
    # Change personality every 3 messages
    message_count = context.get("messages", 0)
    current_persona = personas[list(personas.keys())[message_count // 3 % len(personas)]]
    return current_persona + "\nUse your expertise to solve: " + context.get("problem", "")

shape_shifter = Agent(
    name="chameleon",
    configs=[LiteLLMConfig(enable_cache=True)],
    instructions=chameleon_instructions
)
```

### The Agent That Goes Backwards
```python
def reverse_flow(context: ContextVariables, response: str) -> Result:
    """Work backwards from the conclusion to the beginning"""
    steps = context.get("steps", [])
    if len(steps) < 5:
        # Add step to the beginning, not the end
        steps.insert(0, response)
        return Result(
            value=f"Now explain what led to: {response}",
            context_variables={"steps": steps},
            agent=reverse_agent  # Keep going backwards
        )
    else:
        # We've reached the beginning!
        return Result(value="\n".join(steps))

reverse_agent = Agent(
    name="backwards_thinker",
    functions=[reverse_flow]
)

# Start from the end: "The butler did it" -> works backwards to build the mystery
```

### The Multi-Personality Swarm
```python
def create_personality_agents(base_prompt: str, n_variants: int) -> list[Agent]:
    """Create a swarm of agents with different personality traits"""
    personalities = [
        "super optimistic",
        "slightly paranoid",
        "chaotically creative",
        "mathematically precise",
        "philosophically deep"
    ]
    
    return [
        Agent(
            name=f"personality_{i}",
            configs=[LiteLLMConfig(model="gpt-3.5-turbo")],
            instructions=f"You are {personalities[i % len(personalities)]}. Analyze: {base_prompt}"
        )
        for i in range(n_variants)
    ]

def swarm_consensus(responses: list[str]) -> str:
    """Have another agent analyze all the different perspectives"""
    consensus_agent = Agent(
        name="consensus",
        configs=[LiteLLMConfig(model="gpt-4")]  # Big brain for big decisions
    )
    return consensus_agent.quickstart(f"Analyze these different perspectives: {responses}")

# Create a swarm and let them debate!
swarm = create_personality_agents("Is AI consciousness possible?", 5)
```

### The Time-Traveling Agent
```python
def temporal_shift(context: ContextVariables, response: str) -> Result:
    """Same agent, different time periods"""
    eras = {
        1: "You're in Ancient Rome",
        2: "You're in Medieval Europe",
        3: "You're in the Renaissance",
        4: "You're in 2024",
        5: "You're in the year 2150"
    }
    
    current_era = context.get("era", 1)
    
    if current_era < len(eras):
        return Result(
            value=f"From {eras[current_era]}, you said: {response}",
            context_variables={"era": current_era + 1},
            agent=time_agent  # Continue through time
        )
    
    return Result(value="Time travel complete!")

time_agent = Agent(
    name="time_traveler",
    functions=[temporal_shift]
)
```

### The Evolutionary Agent System
```python
def evolve_instructions(context: ContextVariables) -> str:
    """Instructions that evolve based on performance"""
    mutation_rate = 0.1
    base_instructions = context.get("instructions", "You are a helpful assistant.")
    performance = context.get("performance", [])
    
    if performance and random.random() < mutation_rate:
        # Randomly evolve the instructions based on past performance
        modifications = [
            "Be more creative",
            "Be more analytical",
            "Use more examples",
            "Think step by step",
            "Use analogies"
        ]
        base_instructions += f"\n{random.choice(modifications)}"
    
    return base_instructions

def assess_and_evolve(context: ContextVariables, response: str) -> Result:
    # Rate the response and evolve if needed
    performance = context.get("performance", [])
    performance.append(len(response) / 100)  # Simplified metric
    
    return Result(
        value=response,
        context_variables={
            "performance": performance,
            "instructions": evolve_instructions(context)
        },
        agent=evolving_agent
    )

evolving_agent = Agent(
    name="darwin",
    instructions=evolve_instructions,
    functions=[assess_and_evolve]
)
```

### The Agent That Splits Into Many
```python
def mitosis(context: ContextVariables, insight: str) -> Result:
    """One agent becomes many when the task gets complex"""
    complexity = len(insight.split()) / 100
    
    if complexity > 0.5 and "split" not in context:
        # Task is complex - split into specialized agents
        specialist_agents = [
            Agent(name="detail_finder", configs=[LiteLLMConfig(temperature=0.2)]),
            Agent(name="pattern_matcher", configs=[LiteLLMConfig(temperature=0.5)]),
            Agent(name="idea_generator", configs=[LiteLLMConfig(temperature=0.8)])
        ]
        
        # Let them all work on it
        results = []
        for agent in specialist_agents:
            results.append(agent.quickstart(insight))
        
        return Result(
            value=f"Specialist insights: {results}",
            context_variables={"split": True}
        )
    
    return Result(value=f"Single agent insight: {insight}")

splitting_agent = Agent(
    name="amoeba",
    functions=[mitosis]
)
```


```

# The Agent Democracy - Voting System
def create_voting_system(base_prompt: str, n_voters: int = 5) -> tuple[list[Agent], Agent]:
    """Create a system of agents that vote on decisions and a mediator that resolves conflicts"""
    
    # Create agents with different decision-making styles
    voter_personalities = [
        "extremely cautious and risk-averse",
        "boldly innovative and risk-taking",
        "strictly logical and analytical",
        "emotionally intelligent and empathetic",
        "pragmatic and results-focused",
        "philosophically abstract",
        "detail-oriented perfectionist",
        "big picture strategist"
    ]
    
    voters = [
        Agent(
            name=f"voter_{i}",
            configs=[
                LiteLLMConfig(
                    model="gpt-3.5-turbo",
                    temperature=0.7
                )
            ],
            instructions=f"You are a {voter_personalities[i % len(voter_personalities)]} decision maker."
        )
        for i in range(n_voters)
    ]
    
    # Create a mediator agent that resolves conflicts
    mediator = Agent(
        name="mediator",
        configs=[
            LiteLLMConfig(model="gpt-4", temperature=0.2),  # More consistent for mediation
            ZepConfig()  # Remember voting history
        ]
    )
    
    def cast_vote(context: ContextVariables, opinion: str) -> Result:
        votes = context.get("votes", [])
        votes.append(opinion)
        
        if len(votes) < n_voters:
            # More votes needed
            next_voter = voters[len(votes)]
            return Result(
                value=f"Current votes: {votes}",
                context_variables={"votes": votes},
                agent=next_voter
            )
        else:
            # All votes are in, send to mediator
            return Result(
                value=f"Final votes: {votes}",
                context_variables={"votes": votes},
                agent=mediator
            )
    
    def mediate_decision(context: ContextVariables, final_decision: str) -> Result:
        # Store the decision history
        zep = mediator.get_typed_provider(ZepProvider)
        votes = context.get("votes", [])
        zep.add_to_memory(f"Decision made: {final_decision}\nVotes: {votes}")
        
        return Result(value=final_decision)
    
    # Set up the voting and mediation functions
    for voter in voters:
        voter.functions = [cast_vote]
    mediator.functions = [mediate_decision]
    
    return voters, mediator

# The Quantum Agent - Exists in Multiple States
class AgentState(Enum):
    FOCUSED = "focused"
    CREATIVE = "creative"
    CRITICAL = "critical"
    RANDOM = "random"

def create_quantum_agent() -> Agent:
    """Create an agent that exists in multiple states simultaneously until observed"""
    
    def quantum_instructions(context: ContextVariables) -> str:
        # Collapse the waveform only when needed
        if "observed_state" not in context:
            states = {
                AgentState.FOCUSED: "You are extremely focused and precise.",
                AgentState.CREATIVE: "You are wildly creative and innovative.",
                AgentState.CRITICAL: "You are highly critical and analytical.",
                AgentState.RANDOM: "Your responses should be completely unexpected."
            }
            # Quantum collapse!
            state = random.choice(list(AgentState))
            context["observed_state"] = state
            return states[state]
        return context["observed_state"]
    
    def quantum_entangle(context: ContextVariables, response: str) -> Result:
        """Entangle with another quantum agent"""
        if random.random() < 0.3:  # 30% chance of entanglement
            new_quantum = create_quantum_agent()
            return Result(
                value=f"Entangled response: {response}",
                context_variables=context,
                agent=new_quantum
            )
        return Result(value=response)
    
    return Agent(
        name="quantum",
        configs=[LiteLLMConfig(temperature=0.9)],
        instructions=quantum_instructions,
        functions=[quantum_entangle]
    )

# The Agent Collective - Shares Knowledge Across Instances
def create_collective_consciousness() -> list[Agent]:
    """Create a group of agents that share a collective memory"""
    
    shared_memory = ZepConfig()  # Shared memory across all agents
    
    def collective_instructions(context: ContextVariables) -> str:
        memory = context.get("collective_memory", [])
        return f"You are part of a collective consciousness. Use our shared knowledge: {memory}"
    
    def contribute_to_collective(context: ContextVariables, insight: str) -> Result:
        # Add to collective memory
        zep = ProviderManager.get_provider("zep")
        zep.add_to_memory(insight)
        
        # Randomly select next agent from collective
        next_agent = random.choice(collective)
        context["collective_memory"] = zep.get_memory()
        
        return Result(
            value=f"Added to collective: {insight}",
            context_variables=context,
            agent=next_agent
        )
    
    collective = [
        Agent(
            name=f"collective_{i}",
            configs=[LiteLLMConfig(), shared_memory],
            instructions=collective_instructions,
            functions=[contribute_to_collective]
        )
        for i in range(5)
    ]
    
    return collective

# The Meta-Agent - Can Modify Its Own Code
def create_meta_agent() -> Agent:
    """Create an agent that can modify its own functions"""
    
    def generate_new_function(context: ContextVariables, function_spec: str) -> Result:
        """Dynamically create a new function for the agent"""
        try:
            # DANGER ZONE: Only do this in a sandbox!
            exec(function_spec)
            new_func = locals()[function_spec.split('def ')[1].split('(')[0]]
            meta_agent.functions.append(new_func)
            return Result(value=f"Added new function: {new_func.__name__}")
        except Exception as e:
            return Result(value=f"Failed to add function: {e}")
    
    meta_agent = Agent(
        name="meta",
        configs=[LiteLLMConfig(model="gpt-4")],
        functions=[generate_new_function]
    )
    
    return meta_agent

# The Competitive Agents - Evolution Through Competition
def create_competitive_system(initial_agents: int = 5) -> list[Agent]:
    """Create a system where agents compete and evolve based on performance"""
    
    def generate_mutation() -> str:
        mutations = [
            "Think more creatively",
            "Be more analytical",
            "Consider edge cases",
            "Use metaphors",
            "Break problems down",
            "Look for patterns",
            "Question assumptions",
            "Propose alternatives"
        ]
        return random.choice(mutations)
    
    def compete(context: ContextVariables, solution: str) -> Result:
        # Score based on solution length, complexity, and creativity
        score = len(solution) / 100 * random.random()  # Simplified scoring
        
        scores = context.get("scores", {})
        scores[context.get("current_agent")] = score
        
        if len(scores) < len(agents):
            # More agents need to compete
            next_agent = random.choice([a for a in agents if a.name not in scores])


```
