from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from mcp_use import MCPAgent, MCPClient
import os
# Load environment variables
load_dotenv()

async def get_insurance_codes(description: str) -> str:
    
    config_file = "server/mcp_server.json"
    client = MCPClient.from_config_file(config_file)
    
    # Prompt template
    prompt = f"""Map the below description to relevant CPT Codes, ICD-10-CM Codes, ICD-10-PCS Codes, and HCPCS Codes. Provide your explanation and reasoning.

Patient Description:  
{description}

Important Instructions:

1. ONLY use the codes made available through the cptracks mcp server dataset.

2. DO NOT present any information, suggestion, or code that is not found in the cptracks mcp server dataset.

3. DO NOT use or reference any information from the language model's internal knowledge or external sources.

4. If a relevant code is not found in the provided dataset, state "No relevant code found in dataset" for that section.

Output Format:

Relevant CPT Codes:  
<Code> - <Minified Description> - <Inferred Reason>

Relevant HCPCS Codes:  
<Code> - <Minified Description> - <Inferred Reason>

Relevant ICD-10-CM Codes:  
<Code> - <Minified Description> - <Inferred Reason>

Relevant ICD-10-PCS Codes:  
<Code> - <Minified Description> - <Inferred Reason>"""
    
    try:
        # Initialize MCP client and agent
        client = MCPClient.from_config_file(config_file)
        llm = ChatOpenAI(model="gpt-4o")
        
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,
            memory_enabled=False,
        )
        
        # Get response from agent
        #print(prompt)
        response = await agent.run(prompt)
        return response
        
    except Exception as e:
        return f"Error processing query: {str(e)}"
    
    finally:
        # Clean up
        if client and client.sessions:
            await client.close_all_sessions()
