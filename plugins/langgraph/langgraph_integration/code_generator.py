"""
LangGraph Code Generator

Converts visual workflows into executable LangGraph Python code.
"""

from typing import Dict, Any, List


class LangGraphCodeGenerator:
    """Generate LangGraph Python code from visual workflow"""

    def __init__(self):
        self.imports = set()
        self.node_functions = []
        self.state_fields = {}

    def generate(self, workflow: Dict[str, Any]) -> str:
        """
        Main entry point - generate complete Python code

        Args:
            workflow: Visual workflow definition with nodes and edges

        Returns:
            Complete Python code as string
        """
        self.reset()

        # Extract state schema from nodes
        self._analyze_state(workflow)

        # Generate each section
        imports = self._generate_imports(workflow)
        state_class = self._generate_state_class()
        node_functions = self._generate_node_functions(workflow.get("nodes", []))
        graph_builder = self._generate_graph_builder(workflow)

        # Combine all sections
        code = f"""
{imports}

{state_class}

{chr(10).join(node_functions)}

{graph_builder}
"""
        return code

    def _generate_imports(self, workflow: Dict) -> str:
        """Generate import statements based on nodes used"""
        base_imports = [
            "from typing import TypedDict, Annotated, Any",
            "from langgraph.graph import StateGraph, START, END",
            "from langgraph.graph.message import add_messages",
        ]

        # Add imports based on node types
        for node in workflow.get("nodes", []):
            node_type = node.get("type", "")

            if node_type == "llm":
                provider = node.get("config", {}).get("provider", "openai")
                if provider == "openai":
                    base_imports.append("from langchain_openai import ChatOpenAI")
                elif provider == "anthropic":
                    base_imports.append("from langchain_anthropic import ChatAnthropic")
                elif provider == "google":
                    base_imports.append("from langchain_google_genai import ChatGoogleGenerativeAI")

            elif node_type == "document_loader":
                loader_type = node.get("config", {}).get("loader_type")
                if loader_type == "pdf":
                    base_imports.append("from langchain_community.document_loaders import PyPDFLoader")
                elif loader_type == "web":
                    base_imports.append("from langchain_community.document_loaders import WebBaseLoader")
                elif loader_type == "docx":
                    base_imports.append("from langchain_community.document_loaders import Docx2txtLoader")

            elif node_type == "text_splitter":
                base_imports.append("from langchain.text_splitter import RecursiveCharacterTextSplitter")

            elif node_type == "embedding":
                provider = node.get("config", {}).get("provider", "openai")
                if provider == "openai":
                    base_imports.append("from langchain_openai import OpenAIEmbeddings")

            elif node_type == "vector_store":
                provider = node.get("config", {}).get("provider", "faiss")
                if provider == "faiss":
                    base_imports.append("from langchain_community.vectorstores import FAISS")
                elif provider == "pinecone":
                    base_imports.append("from langchain_pinecone import PineconeVectorStore")
                elif provider == "chroma":
                    base_imports.append("from langchain_community.vectorstores import Chroma")

            elif node_type == "deep_agent":
                base_imports.append("from deepagents import create_deep_agent")

        return "\n".join(sorted(set(base_imports)))

    def _generate_state_class(self) -> str:
        """Generate State TypedDict class"""
        # Always include messages
        fields = ['    messages: Annotated[list, add_messages]']

        # Add other fields
        for field_name, field_type in self.state_fields.items():
            fields.append(f'    {field_name}: {field_type}')

        return f'''
class State(TypedDict):
    """Workflow state"""
{chr(10).join(fields)}
'''

    def _generate_node_functions(self, nodes: List[Dict]) -> List[str]:
        """Generate function for each node"""
        functions = []

        for node in nodes:
            node_type = node.get("type", "")

            if node_type in ["start", "end"]:
                continue

            func_name = self._sanitize_node_id(node.get("id", ""))

            if node_type == "llm":
                functions.append(self._generate_llm_node(func_name, node))
            elif node_type == "function":
                functions.append(self._generate_function_node(func_name, node))
            elif node_type == "document_loader":
                functions.append(self._generate_document_loader_node(func_name, node))
            elif node_type == "text_splitter":
                functions.append(self._generate_text_splitter_node(func_name, node))
            elif node_type == "embedding":
                functions.append(self._generate_embedding_node(func_name, node))
            elif node_type == "vector_store":
                functions.append(self._generate_vector_store_node(func_name, node))
            elif node_type == "deep_agent":
                functions.append(self._generate_deep_agent_node(func_name, node))

        return functions

    def _generate_llm_node(self, func_name: str, node: Dict) -> str:
        """Generate LLM node function"""
        config = node.get("config", {})
        provider = config.get("provider", "openai")
        model = config.get("model", "gpt-4o")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 1000)
        system_prompt = config.get("system_prompt", "").replace('"', '\\"')

        if provider == "openai":
            llm_init = f'ChatOpenAI(model="{model}", temperature={temperature}, max_tokens={max_tokens})'
        elif provider == "anthropic":
            llm_init = f'ChatAnthropic(model="{model}", temperature={temperature}, max_tokens={max_tokens})'
        elif provider == "google":
            llm_init = f'ChatGoogleGenerativeAI(model="{model}", temperature={temperature}, max_tokens={max_tokens})'
        else:
            llm_init = f'ChatOpenAI(model="{model}", temperature={temperature})'

        label = node.get("label", "LLM Node")

        return f'''
def {func_name}(state: State) -> dict:
    """LLM Node: {label}"""
    llm = {llm_init}

    messages = state.get("messages", [])

    # Add system prompt if provided
    system_prompt = """{system_prompt}"""
    if system_prompt and messages:
        if not any(isinstance(m, tuple) and m[0] == "system" for m in messages):
            messages = [("system", system_prompt)] + messages

    response = llm.invoke(messages)
    return {{"messages": [response]}}
'''

    def _generate_function_node(self, func_name: str, node: Dict) -> str:
        """Generate custom function node"""
        code = node.get("config", {}).get("code", "output = input")
        label = node.get("label", "Function Node")

        return f'''
def {func_name}(state: State) -> dict:
    """Function Node: {label}"""
    # User's custom code
    input_data = state.get("input")

    # Execute user code
    local_vars = {{"input": input_data}}
    exec("""
{code}
""", {{}}, local_vars)

    return {{"output": local_vars.get("output")}}
'''

    def _generate_document_loader_node(self, func_name: str, node: Dict) -> str:
        """Generate document loader node"""
        config = node.get("config", {})
        loader_type = config.get("loader_type", "pdf")
        source = config.get("source", "")
        label = node.get("label", "Document Loader")

        if loader_type == "pdf":
            loader_code = f'PyPDFLoader("{source}")'
        elif loader_type == "web":
            loader_code = f'WebBaseLoader("{source}")'
        elif loader_type == "docx":
            loader_code = f'Docx2txtLoader("{source}")'
        else:
            loader_code = f'PyPDFLoader("{source}")'

        return f'''
def {func_name}(state: State) -> dict:
    """Document Loader Node: {label}"""
    loader = {loader_code}
    documents = loader.load()
    return {{"documents": documents}}
'''

    def _generate_text_splitter_node(self, func_name: str, node: Dict) -> str:
        """Generate text splitter node"""
        config = node.get("config", {})
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 200)
        label = node.get("label", "Text Splitter")

        return f'''
def {func_name}(state: State) -> dict:
    """Text Splitter Node: {label}"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size={chunk_size},
        chunk_overlap={chunk_overlap}
    )
    chunks = splitter.split_documents(state.get("documents", []))
    return {{"chunks": chunks}}
'''

    def _generate_embedding_node(self, func_name: str, node: Dict) -> str:
        """Generate embedding node"""
        config = node.get("config", {})
        model = config.get("model", "text-embedding-3-small")
        label = node.get("label", "Embeddings")

        return f'''
def {func_name}(state: State) -> dict:
    """Embedding Node: {label}"""
    embeddings = OpenAIEmbeddings(model="{model}")
    chunks = state.get("chunks", [])
    vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
    return {{"embeddings": vectors, "chunks": chunks}}
'''

    def _generate_vector_store_node(self, func_name: str, node: Dict) -> str:
        """Generate vector store node"""
        config = node.get("config", {})
        provider = config.get("provider", "faiss")
        action = config.get("action", "store")
        index_name = config.get("index_name", "default")
        label = node.get("label", "Vector Store")

        if action == "store":
            return f'''
def {func_name}(state: State) -> dict:
    """Vector Store Node (Store): {label}"""
    vectorstore = FAISS.from_documents(
        state.get("chunks", []),
        state.get("embeddings")
    )
    vectorstore.save_local("{index_name}")
    return {{"vectorstore": vectorstore}}
'''
        else:  # search
            return f'''
def {func_name}(state: State) -> dict:
    """Vector Store Node (Search): {label}"""
    vectorstore = FAISS.load_local("{index_name}", state.get("embeddings"))
    query = state.get("query", "")
    results = vectorstore.similarity_search(query, k=3)
    return {{"search_results": results}}
'''

    def _generate_deep_agent_node(self, func_name: str, node: Dict) -> str:
        """Generate deep agent node"""
        config = node.get("config", {})
        model = config.get("model", "claude-sonnet-4-5-20250929")
        label = node.get("label", "Deep Agent")

        return f'''
def {func_name}(state: State) -> dict:
    """Deep Agent Node: {label}"""
    agent = create_deep_agent(
        model="{model}",
        tools=[],
        max_iterations=10
    )
    messages = state.get("messages", [])
    response = agent.invoke({{"messages": messages}})
    return {{"messages": [response]}}
'''

    def _generate_graph_builder(self, workflow: Dict) -> str:
        """Generate graph building function"""
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        # Build node additions
        node_additions = []
        for node in nodes:
            if node.get("type") in ["start", "end"]:
                continue
            func_name = self._sanitize_node_id(node.get("id", ""))
            node_id = node.get("id", "")
            node_additions.append(f'    graph.add_node("{node_id}", {func_name})')

        # Build edge additions
        edge_additions = []
        for edge in edges:
            source = edge.get("source_node_id", "")
            target = edge.get("target_node_id", "")

            # Handle START and END
            if source == "start":
                edge_additions.append(f'    graph.add_edge(START, "{target}")')
            elif target == "end":
                edge_additions.append(f'    graph.add_edge("{source}", END)')
            else:
                edge_additions.append(f'    graph.add_edge("{source}", "{target}")')

        return f'''
def build_graph():
    """Build and compile the workflow graph"""
    graph = StateGraph(State)

    # Add nodes
{chr(10).join(node_additions) if node_additions else "    pass"}

    # Add edges
{chr(10).join(edge_additions) if edge_additions else "    pass"}

    return graph.compile()

# Create the compiled app
app = build_graph()
'''

    def _sanitize_node_id(self, node_id: str) -> str:
        """Convert node ID to valid Python function name"""
        return f"node_{node_id.replace('-', '_')}"

    def _analyze_state(self, workflow: Dict):
        """Analyze workflow to determine state fields"""
        # Basic state fields always present
        self.state_fields = {
            "input": "Any",
            "output": "Any",
            "query": "str",
        }

        # Add fields based on node types
        for node in workflow.get("nodes", []):
            node_type = node.get("type", "")

            if node_type in ["document_loader", "text_splitter"]:
                self.state_fields["documents"] = "list"
                self.state_fields["chunks"] = "list"
            elif node_type == "embedding":
                self.state_fields["embeddings"] = "list"
            elif node_type == "vector_store":
                self.state_fields["vectorstore"] = "Any"
                self.state_fields["search_results"] = "list"

    def reset(self):
        """Reset generator state"""
        self.imports = set()
        self.node_functions = []
        self.state_fields = {}
