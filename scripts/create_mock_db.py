# FILE: scripts/create_mock_db.py

import csv
import os
import time

from vertexai.language_models import TextEmbeddingModel


def get_embedding(text: str, model_name: str = "text-embedding-004") -> list[float]:
    """Generates an embedding for a given text."""
    model = TextEmbeddingModel.from_pretrained(model_name)
    try:
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except Exception as e:
        print(f"  ERROR: Could not get embedding for '{text[:30]}...': {e}")
        # Return a zero vector on failure so the process doesn't stop
        return [0.0] * 768  # The dimension of text-embedding-004 is 768


def generate_mock_data_with_embeddings():
    """
    Generates a CSV of mock tickets and enriches it with vector embeddings.

    This function processes a predefined list of ADK support tickets, generates
    a vector embedding for each ticket's 'request' text using a Vertex AI
    model, and saves the combined data to 'data/resolved_tickets.csv'.
    """
    print("INFO: Initializing embedding model and generating mock data...")

    # This is the original data for the tickets
    ticket_data = [
        # --- Core Concepts & Orchestration ---
        [
            "ADK-101",
            "DEV-101",
            "How do I make my agents call each other in a specific, multi-step sequence? My main agent just stops after the first step.",
            "Core Concepts",
            "The best practice is to use a strong, sequential prompt for the orchestrator agent. List the tools/sub-agents to be called in order (e.g., Step A, Step B, Step C) and ensure the orchestrator's logic checks the state after each step to decide the next action.",
        ],
        [
            "ADK-102",
            "DEV-102",
            "What is the best way to handle different types of user queries, like greetings vs actual support tickets?",
            "Core Concepts",
            "Implement a 'gatekeeper' or 'intent analysis' pattern in your main orchestrator's prompt. Instruct the agent to first classify the user's intent. If it's a simple conversation, it should answer directly. If it's a technical issue, it should trigger the full tool-calling workflow.",
        ],
        [
            "ADK-103",
            "DEV-103",
            "How should I pass data between different sub-agents in my workflow?",
            "State Management",
            "The orchestrator should manage the data flow. The best pattern is for a sub-agent to return its full result (e.g., a JSON string), which the orchestrator then receives. The orchestrator's reasoning process can then parse this result and pass only the relevant pieces of data as arguments to the next sub-agent in the sequence.",
        ],
        [
            "ADK-104",
            "DEV-115",
            "Can one agent call another agent directly without an orchestrator?",
            "Core Concepts",
            "While technically possible by defining one agent as a tool for another, it is not the recommended pattern. Using a central orchestrator provides better state management, error handling, and clearer logic flow for complex multi-agent systems.",
        ],
        [
            "ADK-105",
            "DEV-121",
            "What's the difference between `LlmAgent` and the base `Agent` class?",
            "Core Concepts",
            "The base `Agent` class provides maximum flexibility and is ideal for complex agents that require custom logic for session management or tool configuration via `start_session` and `infer_tool_config` overrides. `LlmAgent` is a more concise and convenient subclass for simpler agents whose primary role is to call tools based on their prompt, as it handles much of the boilerplate automatically.",
        ],
        # --- Tooling & Integration ---
        [
            "ADK-201",
            "DEV-201",
            "How do I define a tool that takes multiple arguments?",
            "Tool Definition",
            "Define your Python function with standard type-hinted arguments (e.g., `def my_tool(name: str, count: int) -> str:`). The ADK automatically generates the correct OpenAPI schema for the LLM from these type hints. The LLM will then populate the arguments as a dictionary when it calls the tool.",
        ],
        [
            "ADK-202",
            "DEV-210",
            "My agent isn't calling my custom tool. What should I check?",
            "Tool Definition",
            "First, ensure the tool is correctly included in the `tools` list when you instantiate your agent. Second, check your agent's prompt; it must clearly describe what the tool does and provide instructions on when the agent should use it. If the prompt is ambiguous, the agent may not know when to call the tool.",
        ],
        [
            "ADK-203",
            "DEV-211",
            "Is it possible to integrate with an external API like Stripe or Twilio?",
            "Tool Definition",
            "Yes. The standard way is to write a custom Python function tool that acts as a client for the external API. For example, a `send_sms` tool would import the Twilio Python library, initialize the client with your API keys (loaded from environment variables), and then make the necessary API call within the function body.",
        ],
        [
            "ADK-204",
            "DEV-215",
            "How do I use the `MCPToolset` to connect to an external tool server?",
            "Tool Definition",
            "You must instantiate `MCPToolset` with the server's address (e.g., 'localhost:50051') and then pass this instance to your agent using the `toolsets` parameter: `my_agent = Agent(toolsets=[mcp_toolset])`. Ensure this is done in an `async` context.",
        ],
        # --- State & Session Management ---
        [
            "ADK-301",
            "DEV-303",
            "How do I access the user's entire conversation history inside a tool?",
            "State Management",
            "You cannot directly access the full `conversation_history` inside a tool function. The `ToolContext` passed to tools only contains the session `state`. The correct pattern is to have the agent's prompt instruct the LLM to pass relevant information from the conversation history as an argument to the tool call.",
        ],
        [
            "ADK-302",
            "DEV-308",
            "Is the session state persistent? If my app restarts, is the data still there?",
            "State Management",
            "The default `InMemorySessionService` does not persist state across application restarts. For persistence, you must implement your own `SessionService` that connects to a durable backend like Firestore, Redis, or a SQL database. The ADK is designed to be pluggable in this way.",
        ],
        [
            "ADK-303",
            "DEV-310",
            "How can I clear the session state for a user to start over?",
            "State Management",
            "Using the `adk web` interface, you can start a new session by clicking the 'New Session' button, which clears the state. Programmatically, you would call the `session_service.delete_session()` method to remove the session data from your backend.",
        ],
        # --- Deployment & Configuration ---
        [
            "ADK-401",
            "DEV-401",
            "My deployment is failing with a 403 Permission Denied error when trying to deploy my agent to Vertex AI.",
            "Deployment",
            "A 403 error on deployment almost always indicates an IAM permission issue. Ensure that the service account being used for deployment has the 'Vertex AI Admin' and 'Service Account User' roles. Also, check that the specific APIs, like AI Platform API and Cloud Storage API, are enabled in your GCP project.",
        ],
        [
            "ADK-402",
            "DEV-402",
            "My agent is failing with a 404 NOT_FOUND error for a model like `gemini-2.5-pro`.",
            "Configuration",
            "A `404 NOT_FOUND` error for a model means the model name is either incorrect or not available in your specified GCP project and region. Check the official Google Cloud documentation for valid, available model names for your location and update your agent definitions accordingly.",
        ],
        [
            "ADK-403",
            "DEV-405",
            "How do I pass environment variables like API keys to my deployed Agent Engine agent?",
            "Deployment",
            "When using `agent_engines.create()` from the `vertexai` library, you can pass a dictionary of environment variables to the `env_vars` parameter. The deployment script should load these values from a local `.env` file and pass them into the creation call.",
        ],
        [
            "ADK-404",
            "DEV-409",
            "My Cloud Run deployment fails with a 'Visibility check was unavailable' error.",
            "Deployment",
            "This specific error means the Cloud Build service account does not have permission to act as the Cloud Run service agent. You need to run a `gcloud iam service-accounts add-iam-policy-binding` command to grant the `roles/iam.serviceAccountUser` role to your project's Cloud Build service account for the Cloud Run service agent.",
        ],
        # --- Callbacks ---
        [
            "ADK-501",
            "DEV-501",
            "My `before_agent_callback` is throwing an `AttributeError: 'CallbackContext' object has no attribute 'conversation_history'`.",
            "Callbacks",
            "This happens because the `before_agent_callback` receives a lightweight `CallbackContext` which only contains the `state`, not the full `conversation_history`. If you need to access the user's initial query to initialize state, it is more reliable to create a dedicated 'intake' tool that the agent calls as its very first action.",
        ],
        [
            "ADK-502",
            "DEV-502",
            "My callback function `my_func(ctx)` is failing with a `TypeError` about an unexpected keyword argument `callback_context`.",
            "Callbacks",
            "This `TypeError` means the parameter name in your function definition does not match what the ADK framework provides. You must rename your function's parameter to match the framework's keyword. For `before_agent_callback`, the correct signature is `def my_func(callback_context: InvocationContext):`.",
        ],
        # --- RAG & Data Errors ---
        [
            "ADK-601",
            "DEV-601",
            "My RAG tool is failing with a Python error: `TypeError: 'RagContexts' object is not iterable`.",
            "RAG & Data",
            "This error occurs when you incorrectly try to iterate over the main response object from the `vertexai.rag.retrieval_query` function. The correct way to access the retrieved documents is to iterate over the `.contexts` attribute of the response object, like so: `for ctx in response.contexts:`.",
        ],
        [
            "ADK-602",
            "DEV-605",
            "I'm getting a `400 INVALID_ARGUMENT` error saying 'Multiple tools are supported only when they are all search tools'.",
            "Tool Definition",
            "The Google API has a constraint that does not allow mixing the built-in `VertexAiRagRetrieval` tool with other custom Python function tools within the same agent's tool list. The correct pattern is to isolate `VertexAiRagRetrieval` in its own dedicated sub-agent, and then have an orchestrator call that sub-agent as part of a larger workflow.",
        ],
        [
            "ADK-603",
            "DEV-610",
            "My BigQuery tool is failing with a `400 Unrecognized name: request` error from the database.",
            "Tool Definition",
            "This is a standard SQL error caused by column name ambiguity, especially in a `WHERE` clause. The most robust fix is to assign an alias to your table in the `FROM` clause (e.g., `FROM my_dataset.my_table AS t`) and then qualify all column references with that alias (e.g., `WHERE t.column_name = ...`).",
        ],
        [
            "ADK-604",
            "DEV-611",
            "My `setup_rag.py` script fails with an `Unknown field for ImportRagFilesResponse: name` error.",
            "RAG & Data",
            "This error indicates an SDK version mismatch or incorrect usage of the import job object. The `rag.import_files()` function returns an operation reference. You must capture this object, get its `.name` attribute, and then use that name to poll the `rag.get_import_job()` function to get the status.",
        ],
        # --- Dependencies & Setup ---
        [
            "ADK-701",
            "DEV-701",
            "My app is crashing with `ModuleNotFoundError: No module named 'llama_index'` when I try to use the RAG tool.",
            "Dependencies / Setup",
            "The ADK's built-in `VertexAiRagRetrieval` tool has a peer dependency on `llama-index`. To fix this, you must explicitly add `llama-index` to your `pyproject.toml` file and then run `poetry install` to update your environment.",
        ],
        [
            "ADK-702",
            "DEV-705",
            "What is the purpose of the `pyproject.toml` file?",
            "Dependencies / Setup",
            "The `pyproject.toml` file is the modern standard for configuring Python projects. It is used by `poetry` to manage all project dependencies, metadata (like name and version), and build settings, replacing older files like `setup.py` and `requirements.txt`.",
        ],
        [
            "ADK-110",
            "DEV-130",
            "How do I create a streaming response from my agent?",
            "Core Concepts",
            "To enable streaming, you must use an agent that supports it and call the `.stream()` or `.stream_async()` method from your runner. The ADK framework will then yield events as they are generated by the LLM and tools, which you can process in real-time on the client side.",
        ],
        [
            "ADK-220",
            "DEV-225",
            "Can a tool return a complex object, or just a string?",
            "Tool Definition",
            "A tool function should return a JSON-serializable type. This can be a string, a number, a boolean, or a dictionary/list containing these types. For complex data, structure it as a dictionary. The ADK will serialize this to a JSON string before passing it back to the LLM in the conversation history.",
        ],
        [
            "ADK-310",
            "DEV-320",
            "What's the best way to handle API keys for tools?",
            "Configuration",
            "Never hardcode API keys in your tool's source code. The best practice is to store them in environment variables. Use a `.env` file for local development and load them using a library like `python-dotenv`. For deployed agents, configure the environment variables directly in the deployment service (e.g., Agent Engine's `env_vars` or Cloud Run's environment settings).",
        ],
        [
            "ADK-410",
            "DEV-415",
            "My Agent Engine deployment is slow. How can I speed it up?",
            "Deployment",
            "Agent Engine deployment involves building a container, pushing it to a registry, and provisioning infrastructure, which can take several minutes. To speed up iteration, do most of your development and testing locally using `adk run` or `adk web`. Only deploy to Agent Engine when you need to test the final, cloud-based version.",
        ],
        [
            "ADK-510",
            "DEV-511",
            "Can I use a callback to stop a tool call from executing?",
            "Callbacks",
            "Yes. In a `before_tool_callback`, you can return a dictionary. This will cause the ADK to skip the actual tool execution and immediately use the dictionary you returned as the 'tool output' for the LLM's next reasoning step. This is useful for implementing validation, caching, or mock responses.",
        ],
        [
            "ADK-620",
            "DEV-622",
            "How do I choose the right chunk_size for my RAG documents?",
            "RAG & Data",
            "Choosing the right `chunk_size` is a balance. Smaller chunks (e.g., 256-512 characters) provide more precise, targeted results but may lack context. Larger chunks (e.g., 1024-2048) provide better context but might include irrelevant information. For technical documentation, a larger chunk size (around 1024) is often better to keep code examples and their explanations together.",
        ],
        [
            "ADK-801",
            "DEV-801",
            "How do I write an evaluation test for my agent?",
            "Evaluation",
            "Create a JSON file with a list of test cases. Each case should have a `query` (the user input) and a `reference` (the ideal agent response). You can also include `expected_tool_use` to verify that the correct tools are called with the right arguments. Then, use the `AgentEvaluator.evaluate()` function from the ADK, pointing it to your agent module and your test data file.",
        ],
        [
            "ADK-802",
            "DEV-802",
            "My evaluation `tool_trajectory_avg_score` is low. What does that mean?",
            "Evaluation",
            "A low `tool_trajectory_avg_score` means your agent's actual tool calls did not match the `expected_tool_use` in your evaluation data. This could be because it called the wrong tool, called the right tool with the wrong arguments, or failed to call a tool when one was expected. Check your agent's prompt to ensure it has clear instructions for when to use each tool.",
        ],
        [
            "ADK-111",
            "DEV-135",
            "Can an agent have no tools at all?",
            "Core Concepts",
            "Yes, absolutely. An agent without any tools is essentially a conversational LLM with a specific persona and instruction set defined by its prompt. This is useful for creating chatbots, characters, or agents whose only purpose is to answer questions based on their initial prompt and conversation history.",
        ],
        [
            "ADK-221",
            "DEV-230",
            "Is there a way to see the exact prompt being sent to the LLM during an `adk run`?",
            "Debugging",
            "Yes. The ADK runner logs have different levels of verbosity. By default, it's concise, but you can increase the verbosity to see the full request sent to the LLM, including the system prompt, conversation history, and available tool definitions. Check the `adk run --help` command for logging options.",
        ],
        [
            "ADK-311",
            "DEV-325",
            "If I update `tool_context.state`, is that change immediately available to other concurrent users?",
            "State Management",
            "No. The session state is isolated to a specific session ID, which is typically tied to a single user's conversation. Changes made to the state in one user's session will not be visible to another user in a different session.",
        ],
        [
            "ADK-411",
            "DEV-420",
            "Does the ADK deployment to Agent Engine support custom domains?",
            "Deployment",
            "The Vertex AI Agent Engine provides a default URL for your deployed agent. Mapping this to a custom domain is not a direct feature of the ADK deployment script itself but would be handled at the Google Cloud infrastructure level, typically by using a Load Balancer (like Cloud Load Balancing) in front of the Agent Engine endpoint and configuring your DNS records accordingly.",
        ],
        [
            "ADK-511",
            "DEV-515",
            "Can an `after_tool_callback` modify the result of a tool before the LLM sees it?",
            "Callbacks",
            "Yes. The `after_tool_callback` receives the `tool_response` as an argument. You can modify this dictionary within the callback and return the modified version. This new dictionary will then be used as the tool's output in the conversation history, allowing you to sanitize, enrich, or reformat tool results before the agent reasons about them.",
        ],
        [
            "ADK-621",
            "DEV-625",
            "What happens if my RAG search returns no relevant documents?",
            "RAG & Data",
            "If the `VertexAiRagRetrieval` tool finds no documents that meet the similarity threshold, it will return an empty result. Your orchestrator agent's prompt should be designed to handle this gracefully. It can either inform the user that no relevant documentation was found or proceed with the workflow using only the information from other sources, like the BigQuery database.",
        ],
        [
            "ADK-803",
            "DEV-805",
            "What is the `response_match_score` in the evaluation results?",
            "Evaluation",
            "The `response_match_score` measures the semantic similarity between the agent's final text response and the `reference` answer you provided in your test case. It uses a language model to score how closely the meaning and content of the two texts align. A high score means the agent's answer was very similar in meaning to the ideal answer.",
        ],
        [
            "ADK-901",
            "DEV-901",
            "How do I handle binary data, like images or audio, with ADK tools?",
            "Tool Definition",
            "Tools should not return raw binary data directly. The recommended pattern is to have the tool save the binary data to a persistent location (like Google Cloud Storage) and return a reference to it, such as the GCS URI (`gs://...`). The agent or a client application can then use this URI to access the file.",
        ],
        [
            "ADK-112",
            "DEV-140",
            "What's the best practice for managing long and complex prompts?",
            "Core Concepts",
            "For maintainability, store long prompts in a dedicated `prompts.py` file within your agent's package. Use Python's triple-quoted strings to write multi-line prompts. You can also use f-strings to dynamically insert information, like a database schema or the current date, into the prompt before the agent is run.",
        ],
        [
            "ADK-222",
            "DEV-240",
            "My tool uses an SDK that requires initialization (e.g., `boto3.client('s3')`). Where should I do this?",
            "Tool Definition",
            "Avoid initializing clients inside the tool function itself, as it's inefficient to do so on every call. A better pattern is to initialize the client once at the module level (outside the function definition) in your `tools.py` file. This creates a shared client instance that can be reused across all calls to the tool.",
        ],
        [
            "ADK-312",
            "DEV-330",
            "How can I store a complex Python object in the state?",
            "State Management",
            "The session state must be JSON-serializable. If you have a custom Python object (e.g., a Pydantic model or a dataclass), you must first convert it to a dictionary (`.model_dump()` for Pydantic) or a JSON string (`json.dumps()`) before saving it to `tool_context.state`. When you read it back, you'll need to parse the JSON and reconstruct your object.",
        ],
        [
            "ADK-412",
            "DEV-430",
            "How can I check the logs for my deployed Agent Engine agent?",
            "Deployment",
            "You can view the logs for a deployed Vertex AI Agent Engine instance by navigating to the Vertex AI section of the Google Cloud Console. Find your Reasoning Engine, and there should be a 'Logs' tab that integrates with Cloud Logging, showing the output and any errors from your agent's execution.",
        ],
        [
            "ADK-622",
            "DEV-630",
            "My vector search is returning irrelevant results. How can I improve it?",
            "RAG & Data",
            "First, ensure your query is specific and keyword-rich, as we do in the `knowledge_retrieval_agent`. Second, check your distance threshold; a lower threshold (e.g., 0.4) will be stricter and return only very close matches. Third, and most importantly, ensure the data you embedded is clean and high-quality. The quality of your source documents is the biggest factor in search relevance.",
        ],
        [
            "ADK-113",
            "DEV-145",
            "How can I make my agent remember things from previous conversations?",
            "State Management",
            "This requires a persistent `SessionService`. By default, ADK uses an in-memory service that is cleared on restart. To achieve long-term memory, you need to create a custom class that implements the `SessionService` interface and uses a database like Firestore or Redis to `create_session`, `get_session`, `update_session`, and `delete_session`.",
        ],
        [
            "ADK-223",
            "DEV-245",
            "Is there a way to stream a tool's output back to the user as it's being generated?",
            "Tool Definition",
            "Direct streaming from a tool is an advanced use case not supported out-of-the-box. The standard flow is that a tool completes its execution and returns a final result. To achieve a streaming-like effect, the tool would need to save its progress intermittently to a shared resource (like a Firestore document or a Pub/Sub topic) that the client application is listening to, while the agent waits for the final result.",
        ],
        [
            "ADK-804",
            "DEV-810",
            "Can I evaluate just one part of my multi-agent system?",
            "Evaluation",
            "Yes. The `AgentEvaluator` takes an `agent_module` as its target. You can point it directly at a sub-agent's module path (e.g., `adk_copilot.sub_agents.problem_solver`) and provide a test data set tailored specifically to that sub-agent's inputs and expected outputs. This is a great way to test your specialist agents in isolation.",
        ],
        [
            "ADK-902",
            "DEV-905",
            "How does ADK handle authentication for Google Cloud tools like BigQuery?",
            "Authentication",
            "ADK uses Application Default Credentials (ADC). When running locally, it will use the credentials you configured with `gcloud auth application-default login`. When deployed on Google Cloud (like Agent Engine or Cloud Run), it automatically uses the service account associated with that resource. You must ensure this service account has the necessary IAM roles (e.g., 'BigQuery User').",
        ],
        [
            "ADK-114",
            "DEV-150",
            "Can I change the LLM's temperature or other generation parameters?",
            "Configuration",
            "Yes. When you instantiate your agent (e.g., `LlmAgent`), you can pass a `generate_content_config` object. For example: `config = GenerationConfig(temperature=0.9); agent = LlmAgent(model='...', generate_content_config=config)`.",
        ],
        [
            "ADK-224",
            "DEV-250",
            "How do I define a tool with optional parameters?",
            "Tool Definition",
            "Use Python's `Optional` type hint and provide a default value of `None`. For example: `def my_tool(required_arg: str, optional_arg: Optional[int] = None) -> str:`. The ADK will correctly generate a schema where `required_arg` is required and `optional_arg` is not. The LLM will only provide the argument if it's relevant.",
        ],
        [
            "ADK-313",
            "DEV-335",
            "What is the difference between `tool_context.state` and `session.state`?",
            "State Management",
            "They generally refer to the same underlying state dictionary for a given session. `tool_context.state` is the property you use to access and modify the state from within a tool function. `session.state` is used when you are interacting with the session object directly, for instance in a custom runner or an external application managing the session lifecycle.",
        ],
        [
            "ADK-413",
            "DEV-435",
            "My deployment fails with a dependency conflict. How do I resolve this?",
            "Dependencies / Setup",
            "This is a common issue with complex Python projects. First, run `poetry lock` to see if Poetry can resolve the conflict automatically. If not, examine the error message to see which two packages require different versions of a third package. You may need to manually adjust the version constraints in your `pyproject.toml` (e.g., change `^1.0` to `~1.2`) to find a compatible set of versions. Running `poetry show` can help you visualize the dependency tree.",
        ],
        [
            "ADK-623",
            "DEV-635",
            "Can the RAG tool search across multiple PDF files at once?",
            "RAG & Data",
            "Yes. When you set up the `VertexAiRagRetrieval` tool, you provide it with a `rag_corpus` resource name. That corpus can have many files imported into it. When you call the tool with a query, the RAG engine will perform a vector search across all the chunks from all the files within that single corpus and return the most relevant results regardless of which source file they came from.",
        ],
        [
            "ADK-805",
            "DEV-815",
            "How can I test an agent that asks for user confirmation, like the two-step code generator?",
            "Evaluation",
            "This is challenging for fully automated evaluation. The standard `AgentEvaluator` is best for single-shot interactions. To test a multi-turn flow, you would typically write a custom Python script using `pytest`. Your script would first send the initial request, then use an `assert` to check that the agent's response is the expected confirmation question. Then, your script would send the 'yes' confirmation and assert that the final response contains the generated code.",
        ],
        [
            "ADK-903",
            "DEV-910",
            "Is there a way to add a tool to an agent after it has been initialized?",
            "Core Concepts",
            "No, the set of tools an agent can use is fixed at instantiation time via the `tools` or `toolsets` parameter. This is because the tool definitions are sent to the LLM as part of the system prompt to enable its reasoning. To change an agent's tools, you would need to create a new agent instance with the updated tool list.",
        ],
    ]

    # Prepare the header row for the CSV file
    header = [
        "ticket_id",
        "customer_id",
        "request",
        "category",
        "suggested_solution",
        "request_embedding",
    ]

    # This list will hold all rows for the final CSV
    output_data = [header]

    # Process each ticket
    for i, row in enumerate(ticket_data):
        request_text = row[2]
        print(
            f"  Generating embedding for ticket {row[0]} ({i+1}/{len(ticket_data)})..."
        )
        embedding = get_embedding(request_text)

        # Append the embedding to the row
        new_row = row + [embedding]
        output_data.append(new_row)

        # Adding a small delay to avoid hitting API rate limits
        time.sleep(1)

    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, "resolved_tickets.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_data)

    print(
        f"✅ Mock database with embeddings created at '{filepath}' with {len(output_data)-1} tickets."
    )


if __name__ == "__main__":
    import vertexai
    from dotenv import load_dotenv

    load_dotenv()
    # Initialize Vertex AI
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    vertexai.init(project=project_id, location=location)

    generate_mock_data_with_embeddings()
