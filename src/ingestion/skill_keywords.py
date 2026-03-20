"""Comprehensive keyword→skill mapping for code-based skill detection.

Each key is a human-readable skill/category tag.
Values are lists of lowercase patterns to match against file content, imports, and filenames.
"""

SKILL_MAP = {
    # --- AI / ML ---
    "LLM Integration": ["openai", "anthropic", "langchain", "llamaindex", "llama_index", "cohere", "huggingface", "transformers"],
    "Multi-Agent Orchestration": ["autogen", "crewai", "multi-agent", "agent_communication", "acp_sdk", "beeai", "langgraph"],
    "RAG": ["chromadb", "chroma", "pinecone", "weaviate", "qdrant", "faiss", "retrieval", "vector_store", "vectorstore"],
    "Prompt Engineering": ["system_prompt", "few_shot", "chain_of_thought", "prompt_template", "jinja2"],
    "Fine-Tuning": ["peft", "lora", "qlora", "trainer", "sft_trainer", "fine_tun", "bitsandbytes"],
    "Embeddings": ["sentence_transformers", "embedding", "openai.embeddings", "text-embedding", "all-minilm"],
    "NLP": ["nltk", "spacy", "tokeniz", "sentiment", "ner", "named_entity"],
    "Computer Vision": ["opencv", "cv2", "torchvision", "yolo", "detectron", "pillow", "pil"],
    "PyTorch": ["torch", "pytorch", "nn.module", "nn.linear", "autograd"],
    "TensorFlow": ["tensorflow", "tf.keras", "keras"],
    "scikit-learn": ["sklearn", "scikit-learn", "randomforest", "gradientboosting", "gridsearchcv", "train_test_split"],
    "MLOps": ["mlflow", "wandb", "weights_and_biases", "model_registry", "experiment_tracking"],
    "Model Serving": ["triton", "torchserve", "onnx", "tensorrt", "model_serving", "inference_server"],

    # --- Cloud / Infrastructure ---
    "AWS": ["boto3", "aws", "s3", "ec2", "lambda", "sagemaker", "dynamodb", "cloudformation", "ecs", "eks", "sqs", "sns"],
    "GCP": ["google.cloud", "bigquery", "cloud_run", "gcs", "google-cloud"],
    "Azure": ["azure", "azure.storage", "azure.identity"],
    "Docker": ["docker", "dockerfile", "docker-compose", "containeriz", "aiodocker"],
    "Kubernetes": ["kubernetes", "k8s", "kubectl", "helm", "pod", "deployment.yaml"],
    "Terraform": ["terraform", "hcl", "infrastructure_as_code", "iac", "pulumi"],
    "CI/CD": ["github_actions", "jenkins", "gitlab_ci", "circleci", "workflow", ".github/workflows"],

    # --- Backend / Systems ---
    "FastAPI": ["fastapi", "uvicorn", "starlette"],
    "Django": ["django", "django.db", "django.http"],
    "Flask": ["flask", "flask_restful"],
    "Express.js": ["express", "app.get(", "app.post(", "router.get("],
    "REST API Design": ["openapi", "swagger", "api_router", "endpoint"],
    "GraphQL": ["graphql", "apollo", "gql", "schema.graphql"],
    "gRPC": ["grpc", "protobuf", "proto"],
    "WebSocket": ["websocket", "socket.io", "socketio", "ws://", "wss://"],
    "Message Queues": ["rabbitmq", "pika", "kafka", "celery", "redis_streams", "nats", "amqp"],
    "Async Programming": ["asyncio", "async def", "await", "aiohttp", "httpx", "aiodocker"],
    "Microservices": ["microservice", "service_mesh", "istio", "envoy", "api_gateway"],
    "Event-Driven Architecture": ["event_driven", "pub_sub", "event_sourcing", "cqrs", "event_bus"],
    "Distributed Systems": ["distributed", "consensus", "replication", "sharding", "partitioning"],

    # --- Frontend ---
    "React": ["react", "jsx", "usestate", "useeffect", "usecallback", "useref", "react-dom"],
    "Next.js": ["next", "next/router", "next/image", "getserversideprops", "next.config"],
    "Vue.js": ["vue", "vuex", "pinia", "v-model", "v-for", "composition api"],
    "TypeScript": ["typescript", ": string", ": number", ": boolean", "interface ", "type "],
    "Tailwind CSS": ["tailwind", "tailwindcss", "tw-", "className=\""],
    "D3.js": ["d3", "d3-selection", "d3-scale", "d3-axis", "d3-geo", "d3-force"],
    "Three.js / WebGL": ["three", "three.js", "webgl", "glsl", "shader", "react-three"],
    "State Management": ["redux", "zustand", "pinia", "vuex", "recoil", "mobx", "tanstack"],
    "SSR / SSG": ["getserversideprops", "getstaticprops", "server-side render", "static site"],
    "Component Libraries": ["material-ui", "mui", "shadcn", "radix", "chakra", "ant-design"],

    # --- Data Engineering ---
    "Data Pipelines": ["airflow", "dagster", "prefect", "luigi", "data_pipeline", "etl_pipeline", "_etl", "etl_", "elt"],
    "Apache Spark": ["pyspark", "spark", "sparksql", "spark_session"],
    "Apache Kafka": ["kafka", "confluent", "kafka_consumer", "kafka_producer"],
    "Data Warehousing": ["snowflake", "redshift", "bigquery", "databricks", "delta_lake", "iceberg"],
    "dbt": ["dbt", "dbt_project", "data_build_tool"],
    "Pandas": ["pandas", "dataframe", "pd.read", "pd.merge", "groupby"],
    "Data Modeling": ["star_schema", "dimensional", "normalization", "data_model"],
    "Parquet / Arrow": ["parquet", "pyarrow", "arrow", "columnar"],

    # --- Security ---
    "Penetration Testing": ["pentest", "metasploit", "exploit", "payload", "nmap", "burp", "gobuster", "ffuf"],
    "OWASP": ["owasp", "xss", "csrf", "sql_injection", "injection", "ssrf"],
    "Vulnerability Assessment": ["cve", "vulnerability", "nikto", "nessus", "nuclei", "trivy"],
    "Network Security": ["wireshark", "tcpdump", "firewall", "ids", "ips", "pcap", "snort"],
    "Cryptography": ["encryption", "aes", "rsa", "tls", "ssl", "hashlib", "bcrypt", "jwt", "pkcs"],
    "MITRE ATT&CK": ["mitre", "att&ck", "tactic", "technique", "t1059", "lateral_movement"],
    "DevSecOps": ["devsecops", "sast", "dast", "snyk", "semgrep", "bandit", "sonarqube"],
    "Secrets Management": ["vault", "hashicorp", "secrets", "kms", "secret_manager"],
    "Credential Harvesting": ["mimikatz", "credential", "ntlm", "kerberos", "pass_the_hash", "bloodhound"],

    # --- DevOps / SRE ---
    "Observability": ["prometheus", "grafana", "datadog", "opentelemetry", "otel", "jaeger"],
    "Logging": ["elk", "elasticsearch", "logstash", "kibana", "fluentd", "structured_logging"],
    "Monitoring": ["alertmanager", "pagerduty", "new_relic", "sentry", "error_tracking"],
    "Infrastructure Automation": ["ansible", "puppet", "chef", "salt", "configuration_management"],

    # --- Database ---
    "PostgreSQL": ["postgresql", "postgres", "psycopg", "asyncpg", "pg_"],
    "Neo4j": ["neo4j", "cypher", "graph_database", "knowledge_graph"],
    "Redis": ["redis", "aioredis", "redis_cache", "celery"],
    "MongoDB": ["mongodb", "pymongo", "mongoose", "nosql"],
    "DuckDB": ["duckdb", "analytical_database", "olap"],
    "SQLAlchemy": ["sqlalchemy", "alembic", "orm", "session.query"],
    "Vector Databases": ["pinecone", "weaviate", "qdrant", "chroma", "milvus", "vector_index"],
    "Elasticsearch": ["elasticsearch", "elastic", "kibana", "lucene", "full_text_search"],

    # --- Software Engineering ---
    "Testing": ["pytest", "unittest", "jest", "vitest", "mocha", "cypress", "playwright", "test_", "_test.py"],
    "Design Patterns": ["factory_pattern", "abstract_factory", "singleton", "observer", "strategy", "adapter", "decorator_pattern"],
    "API Design": ["openapi", "swagger", "api_spec", "schema_validation", "pydantic"],
    "Performance Optimization": ["profiling", "benchmark", "caching", "memoiz", "lazy_load"],

    # --- Emerging / Hot ---
    "MCP Protocol": ["mcp", "model_context_protocol", "mcp_server", "mcp_tool"],
    "Agentic AI": ["ai_agent", "react_agent", "agent_executor", "autonomous", "tool_calling", "function_calling", "task_tree"],
    "Streaming / SSE": ["server_sent_events", "sse", "streaming", "event_stream", "text/event-stream"],
    "Real-Time Systems": ["real_time", "realtime", "live_update", "push_notification"],

    # --- Domain-Specific ---
    "Geospatial": ["haversine", "geospatial", "geopy", "shapely", "geopandas", "osm", "overpass", "geojson"],
    "Financial / Trading": ["trading", "backtest", "candlestick", "portfolio", "alpha_vantage", "ccxt"],
    "PDF Processing": ["pypdf", "pdfplumber", "pdfminer", "pdf_processing", "ocr", "tesseract"],
    "Web Scraping": ["scrapy", "beautifulsoup", "selenium", "playwright", "requests_html", "httpx"],
    "Audio / Signal Processing": ["audio", "fft", "web_audio", "analyser", "frequency", "waveform"],
}
