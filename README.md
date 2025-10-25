# Azure AI Foundry Agent Service - Browser Automation Setup Guide

## Overview

This guide walks you through setting up the **Azure AI Foundry Agent Service** with the **Browser Automation Tool**. This approach is different from the previous demo - instead of running Playwright locally, the browser automation runs in a cloud-hosted, isolated environment managed by Azure Playwright Workspaces.

## Key Differences from Previous Approach

| Aspect | Previous Approach (`final_working_demo.py`) | Agent Service Approach |
|--------|---------------------------------------------|------------------------|
| **Browser Execution** | Local Playwright on your machine | Cloud-hosted in Azure Playwright Workspaces |
| **SDK Used** | Azure OpenAI SDK (`openai` package) | Azure AI Agents SDK (`azure-ai-agents`) |
| **Architecture** | Direct API calls to Azure OpenAI | Agent Service with Browser Automation Tool |
| **Browser Management** | You manage browser lifecycle | Azure manages browser sessions |
| **Isolation** | Runs on your machine | Sandboxed cloud environment |
| **Scalability** | Limited to local resources | Scales in Azure cloud |

## Prerequisites

### 1. Azure Resources Required

- **Azure AI Foundry Project** 
- **Playwright Workspace** 
- **Azure OpenAI Model Deployment** 

### 2. Required Permissions

- **Contributor** role on the Playwright Workspace resource
- Access to create connections in AI Foundry portal

## Step-by-Step Setup

### Step 1: Create Playwright Workspace

1. **Go to Azure Portal**: https://portal.azure.com

2. **Create Resource**:
   - Click "Create a resource"
   - Search for "Playwright Workspace" or "Microsoft Playwright Testing"
   - Click "Create"

3. **Configure the Workspace**:
   ```
   Subscription: [Your subscription]
   Resource Group: [Same as your AI Foundry project]
   Region: East US 2 (same as your AI Foundry resources)
   Workspace Name: playwright-workspace-demo
   Pricing Tier: Standard
   ```

4. **Create and Wait**:
   - Click "Review + Create"
   - Click "Create"
   - Wait for deployment to complete (~2 minutes)

### Step 2: Get Playwright Workspace Details

1. **Navigate to your Playwright Workspace**

2. **Go to "Workspace Details" or "Get Started" page**

3. **Copy the following**:
   - **Workspace Region Endpoint**: 
     - Format: `wss://eastus2.api.playwright.microsoft.com/playwrightworkspaces/{workspaceId}/browsers`
     - Example: `wss://eastus2.api.playwright.microsoft.com/playwrightworkspaces/abc123/browsers`
   - **Note**: The URL starts with `wss://` (WebSocket Secure), not `https://`

4. **Generate Access Token**:
   - Go to "Access Tokens" section
   - Click "+ Create"
   - Name: "ai-agent-token"
   - Click "Generate"
   - **Copy the token immediately** (you won't see it again!)

### Step 3: Assign Permissions

1. **In your Playwright Workspace**, go to "Access Control (IAM)"

2. **Add role assignment**:
   - Role: "Contributor"
   - Assign access to: "User, group, or service principal"
   - Select: Your user account (or the managed identity of your AI Foundry project)
   - Click "Save"

### Step 4: Create Connection in AI Foundry Portal

1. **Go to AI Foundry Portal**: https://ai.azure.com/

2. **Select your project** (the one with endpoint containing "admin-9338-kk-resource")

3. **Navigate to Management Center**:
   - In the left sidebar, click "Management center"
   - Click "Connected resources"

4. **Create New Connection**:
   - Click "+ New connection"
   - Connection type: **"Serverless Model"**
   
5. **Fill in Connection Details**:
   ```
   Connection name: playwright-connection
   Target URI: [Paste the Playwright endpoint from Step 2]
              (e.g., wss://eastus2.api.playwright.microsoft.com/playwrightworkspaces/abc123/browsers)
   Authentication: API Key
   Key: [Paste the access token from Step 2]
   ```

6. **Save the Connection**:
   - Click "Create"
   - **Copy the connection name** (you'll use it as an environment variable)

### Step 5: Set Environment Variables


```powershell
[System.Environment]::SetEnvironmentVariable('PROJECT_ENDPOINT', 'your-value-here', 'User')
[System.Environment]::SetEnvironmentVariable('AZURE_PLAYWRIGHT_CONNECTION_NAME', 'playwright-connection', 'User')
[System.Environment]::SetEnvironmentVariable('MODEL_DEPLOYMENT_NAME', 'gpt-4.1', 'User')
```

### Step 6: Install Required Packages

```powershell
pip install azure-ai-agents>=1.2.0b2
pip install azure-ai-projects
pip install azure-identity
```

### Step 7: Run the Demo

```powershell
python agent_service_browser_automation.py
```

## Expected Output

When successful, you'll see:

```
🔧 Initializing Azure AI Foundry Project Client...
🔗 Retrieving Playwright connection: playwright-connection
✅ Connected! Connection ID: /subscriptions/.../connections/playwright-connection

🤖 Creating AI Agent with Browser Automation tool...
✅ Agent created! Agent ID: asst_abc123

💬 Creating conversation thread...
✅ Thread created! Thread ID: thread_xyz789

📝 Sending task to agent...
✅ Message created! Message ID: msg_123456

⏳ Agent is working... This may take a minute as it navigates the website...
   (The agent will launch a browser, search for MSFT, and extract the data)

✅ Agent run completed! Status: completed

📊 Browser Automation Steps:
================================================================================

Step 1 - Status: completed

  🌐 Browser Automation Tool Call:
     Input: Navigate to finance.yahoo.com and search for MSFT...
     Output: Successfully found Microsoft stock data

     Browser Steps:
       1. Last result: Navigated to finance.yahoo.com
          Current state: On Yahoo Finance homepage
          Next step: Search for MSFT
       2. Last result: Entered MSFT in search
          Current state: On MSFT stock page
          Next step: Click YTD button
       3. Last result: Clicked YTD
          Current state: Chart showing YTD data
          Next step: Extract percentage

================================================================================
🎯 Agent's Final Response:
================================================================================

Microsoft (MSFT) has a year-to-date stock price change of +23.4%.

```

