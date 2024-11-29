sequenceDiagram
    participant U as User
    participant S as Schwarm
    participant A as Agent
    participant PM as ProviderManager
    participant LP as LLM Provider
    participant EP as Event Provider
    participant TH as Tool Handler

    U->>S: quickstart(agent, input)
    S->>PM: create_provider_and_register()
    S->>PM: trigger_event(START)
    PM->>EP: handle_event(START)
    
    loop Until max_turns or completion
        S->>S: _complete_agent_request()
        S->>PM: trigger_event(INSTRUCT)
        PM->>EP: handle_event(INSTRUCT)
        
        S->>PM: get_first_llm_provider()
        PM->>LP: complete(messages, tools)
        LP-->>S: completion
        
        alt Has tool_calls
            S->>TH: handle_tool_calls()
            TH-->>S: tool_response
            
            alt Agent handoff
                S->>A: switch active agent
            end
        end
    end
    
    S-->>U: Response(messages, agent, context)
