"""
Azure AI Foundry Agent Service with Browser Automation Tool
=============================================================

This demo shows how to use the Browser Automation tool with Azure AI Foundry Agent Service.

Prerequisites:
1. Create a Playwright Workspace in Azure Portal
   - Navigate to Azure Portal > Create Resource > Search for "Playwright Workspace"
   - Create the workspace and note the region
   
2. Generate Playwright Access Token
   - In the Playwright Workspace, go to "Access Tokens"
   - Create a new token and copy it
   
3. Get the Playwright Workspace Region Endpoint
   - In Playwright Workspace > Workspace Details
   - Copy the endpoint (format: wss://{region}.api.playwright.microsoft.com/playwrightworkspaces/{workspaceId}/browsers)
   
4. Create Connection in Azure AI Foundry Portal
   - Go to your AI Foundry project: https://ai.azure.com/
   - Navigate to Management Center > Connected Resources
   - Create new "Serverless Model" connection:
     * Target URI: The Playwright workspace endpoint (starts with wss://)
     * Key: Your Playwright access token
     * Save the connection name
   
5. Set Environment Variables:
   - PROJECT_ENDPOINT: Your AI Foundry project endpoint
   - AZURE_PLAYWRIGHT_CONNECTION_NAME: Name of the connection created in step 4
   - MODEL_DEPLOYMENT_NAME: Your model deployment name (e.g., gpt-4.1)
   - AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED: Set to "true" to capture message content in traces (optional)

Installation:
    pip install azure-ai-agents>=1.2.0b2
    pip install azure-ai-projects
    pip install azure-identity
    pip install azure-monitor-opentelemetry
"""

import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    MessageRole,
    RunStepToolCallDetails,
    RunStepBrowserAutomationToolCall,
)
from azure.ai.agents.telemetry import AIAgentsInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

def main():
    """Run the browser automation demo using Azure AI Foundry Agent Service."""
    
    # Verify required environment variables
    required_vars = [
        "PROJECT_ENDPOINT",
        "AZURE_PLAYWRIGHT_CONNECTION_NAME", 
        "MODEL_DEPLOYMENT_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables before running.")
        print("\nExample:")
        print('$env:PROJECT_ENDPOINT = "https://your-project.services.ai.azure.com/api/projects/your-project-id"')
        print('$env:AZURE_PLAYWRIGHT_CONNECTION_NAME = "playwright-connection"')
        print('$env:MODEL_DEPLOYMENT_NAME = "gpt-4.1"')
        print('\nOptional (for tracing):')
        print('$env:AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED = "true"')
        return
    
    # Enable content recording for traces (optional)
    if not os.getenv("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"):
        os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
        print("✅ Enabled trace content recording")
    
    # Create AI Project Client
    print("🔧 Initializing Azure AI Foundry Project Client...")
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential()
    )
    
    # Configure tracing
    print("📊 Setting up tracing...")
    tracing_enabled = False
    try:
        # Get Application Insights connection string
        connection_string = project_client.telemetry.get_application_insights_connection_string()
        
        if connection_string:
            print(f"   Found Application Insights connection")
            print(f"   Connection string: {connection_string[:50]}...")
            
            # Configure Azure Monitor for tracing
            configure_azure_monitor(connection_string=connection_string)
            
            # Instrument the AI Agents SDK
            AIAgentsInstrumentor().instrument()
            
            tracing_enabled = True
            print(f"✅ Tracing enabled! View traces at: https://ai.azure.com/")
            print(f"   Navigate to your project > Tracing")
            print(f"   Note: Traces may take 1-2 minutes to appear in the portal")
        else:
            print("⚠️  No Application Insights connected. Tracing disabled.")
            print("\n   📋 To enable tracing:")
            print("   1. Go to https://ai.azure.com/")
            print("   2. Select your project")
            print("   3. Go to 'Tracing' in the left sidebar")
            print("   4. Click 'Connect' or 'Create new' Application Insights resource")
            print("   5. Wait for connection to complete")
            print("   6. Re-run this script")
    except Exception as e:
        print(f"⚠️  Could not enable tracing: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Details: {traceback.format_exc()}")
        print("   Continuing without tracing...")
    
    # Get tracer for custom spans
    tracer = trace.get_tracer(__name__)
    
    try:
        with project_client:
            # Start tracing span for the entire demo
            with tracer.start_as_current_span("browser_automation_demo"):
                # Get the Playwright connection
                print(f"\n🔗 Retrieving Playwright connection: {os.environ['AZURE_PLAYWRIGHT_CONNECTION_NAME']}")
                playwright_connection = project_client.connections.get(
                    name=os.environ["AZURE_PLAYWRIGHT_CONNECTION_NAME"]
                )
                print(f"✅ Connected! Connection ID: {playwright_connection.id}")
                
                # Create agent with Browser Automation tool
                print("\n🤖 Creating AI Agent with Browser Automation tool...")
                with tracer.start_as_current_span("create_agent"):
                    agent = project_client.agents.create_agent(
                        model=os.environ["MODEL_DEPLOYMENT_NAME"],
                        name="browser-automation-agent",
                        instructions="""You are a helpful assistant with browser automation capabilities.
                        You can navigate websites, extract information, and interact with web pages.
                        Use the browser automation tool to complete tasks as requested.""",
                        tools=[{
                            "type": "browser_automation",
                            "browser_automation": {
                                "connection": {
                                    "id": playwright_connection.id,
                                }
                            }
                        }],
                    )
                    print(f"✅ Agent created! Agent ID: {agent.id}")
                
                # Create a thread for conversation
                print("\n💬 Creating conversation thread...")
                with tracer.start_as_current_span("create_thread"):
                    thread = project_client.agents.threads.create()
                    print(f"✅ Thread created! Thread ID: {thread.id}")
                
                # Create a message with the task
                print("\n📝 Sending task to agent...")
                task_message = """
                Your goal is to report the Microsoft year-to-date stock price change.
                
                To do that:
                1. Go to the website finance.yahoo.com
                2. At the top of the page, find the search bar
                3. Enter 'MSFT' to get Microsoft stock information
                4. On the resulting page, find the default chart showing Microsoft stock price
                5. Click on 'YTD' at the top of that chart
                6. Report the percent value that shows below the chart
                
                Please complete this task and provide me with the YTD percentage change.
                """
                
                with tracer.start_as_current_span("create_message"):
                    message = project_client.agents.messages.create(
                        thread_id=thread.id,
                        role=MessageRole.USER,
                        content=task_message
                    )
                    print(f"✅ Message created! Message ID: {message.id}")
                
                # Create and process the agent run
                print("\n⏳ Agent is working... This may take a minute as it navigates the website...")
                print("   (The agent will launch a browser, search for MSFT, and extract the data)")
                
                with tracer.start_as_current_span("agent_run"):
                    # Add custom attributes to the span
                    current_span = trace.get_current_span()
                    current_span.set_attribute("agent.id", agent.id)
                    current_span.set_attribute("thread.id", thread.id)
                    current_span.set_attribute("task.type", "stock_price_extraction")
                    
                    run = project_client.agents.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=agent.id
                    )
                    
                    # Record run status in span
                    current_span.set_attribute("run.status", run.status)
                    current_span.set_attribute("run.id", run.id)
                
                print(f"\n✅ Agent run completed! Status: {run.status}")
                
                if run.status == "failed":
                    print(f"❌ Run failed: {run.last_error}")
                    return
                
                # Get the run steps to see browser automation details
                print("\n📊 Browser Automation Steps:")
                print("=" * 80)
                run_steps = project_client.agents.run_steps.list(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                for step_num, step in enumerate(run_steps, 1):
                    print(f"\nStep {step_num} - Status: {step.status}")
                    
                    if isinstance(step.step_details, RunStepToolCallDetails):
                        tool_calls = step.step_details.tool_calls
                        
                        for call in tool_calls:
                            if isinstance(call, RunStepBrowserAutomationToolCall):
                                print(f"\n  🌐 Browser Automation Tool Call:")
                                print(f"     Input: {call.browser_automation.input}")
                                print(f"     Output: {call.browser_automation.output}")
                                
                                if hasattr(call.browser_automation, 'steps') and call.browser_automation.steps:
                                    print(f"\n     Browser Steps:")
                                    for i, browser_step in enumerate(call.browser_automation.steps, 1):
                                        print(f"       {i}. Last result: {browser_step.last_step_result}")
                                        print(f"          Current state: {browser_step.current_state}")
                                        print(f"          Next step: {browser_step.next_step}")
                
                # Get the agent's final response
                print("\n" + "=" * 80)
                print("🎯 Agent's Final Response:")
                print("=" * 80)
                
                response_message = project_client.agents.messages.get_last_message_by_role(
                    thread_id=thread.id,
                    role=MessageRole.AGENT
                )
                
                if response_message:
                    for text_message in response_message.text_messages:
                        print(f"\n{text_message.text.value}")
                    
                    # Print any URL citations
                    if response_message.url_citation_annotations:
                        print("\n📎 Citations:")
                        for annotation in response_message.url_citation_annotations:
                            print(f"   - {annotation.url_citation.title}: {annotation.url_citation.url}")
                
                # Keep the agent for reuse
                print(f"\n💾 Agent preserved for future use!")
                print(f"   Agent ID: {agent.id}")
                print(f"   Thread ID: {thread.id}")
                print(f"\n   You can reuse this agent in future runs.")
                
                print("\n✨ Demo completed successfully!")
                
                if tracing_enabled:
                    print("\n📊 View detailed traces at: https://ai.azure.com/")
                    print("   Navigate to: Your Project > Tracing")
                    print("   You'll see timeline, browser actions, and performance metrics!")
                    print("\n   ⏱️  Note: Traces can take 1-2 minutes to appear in Application Insights")
                    print("   💡 Tip: Refresh the Tracing page if you don't see them immediately")
                else:
                    print("\n⚠️  Tracing was not enabled for this run.")
                    print("   Connect Application Insights in the portal to enable tracing.")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure you have created a Playwright Workspace in Azure Portal")
        print("2. Verify the connection is created in AI Foundry portal under Connected Resources")
        print("3. Check that your PROJECT_ENDPOINT is correct")
        print("4. Ensure your identity has 'Contributor' role on the Playwright Workspace")
        raise


if __name__ == "__main__":
    main()
