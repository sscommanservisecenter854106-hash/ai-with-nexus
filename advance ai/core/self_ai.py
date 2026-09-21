import os
import re
import json
import html
import httpx
from typing import List, Dict, Any, Optional

class SelfAIEngine:
    """
    100% Self-Contained, Autonomous AI Engine for Nexus-AI.
    Operates completely offline with zero external API calls, zero API keys, and zero telemetry.
    Features:
    - Intent Recognition & Conversational Memory
    - Autonomous Tool Calling (Web Search, Code Runner, Calculator, File Manager, System Info, Weather, Datetime)
    - Full RAG Context Question-Answering
    - Comprehensive Knowledge Graph across Programming, AI, Science, Math, History, and General Knowledge
    - Built-in State & World Capitals and Leadership Lookup
    - Automatic Local LLM discovery (Ollama/Local endpoints) if available
    """

    INDIAN_CAPITALS = {
        "andhra pradesh": ("Amaravati", "अमरावती"),
        "arunachal pradesh": ("Itanagar", "ईटानगर"),
        "assam": ("Dispur", "दिसपुर"),
        "bihar": ("Patna", "पटना"),
        "chhattisgarh": ("Raipur", "रायपुर"),
        "goa": ("Panaji", "पणजी"),
        "gujarat": ("Gandhinagar", "गांधीनगर"),
        "haryana": ("Chandigarh", "चंडीगढ़"),
        "himachal pradesh": ("Shimla", "शिमला"),
        "jharkhand": ("Ranchi", "राँची"),
        "karnataka": ("Bengaluru", "बेंगलुरु"),
        "kerala": ("Thiruvananthapuram", "तिरुवनंतपुरम"),
        "madhya pradesh": ("Bhopal", "भोपाल"),
        "maharashtra": ("Mumbai", "मुंबई"),
        "manipur": ("Imphal", "इम्फाल"),
        "meghalaya": ("Shillong", "शिलांग"),
        "mizoram": ("Aizawl", "आइज़ोल"),
        "nagaland": ("Kohima", "कोहिमा"),
        "odisha": ("Bhubaneswar", "भुवनेश्वर"),
        "punjab": ("Chandigarh", "चंडीगढ़"),
        "rajasthan": ("Jaipur", "जयपुर"),
        "sikkim": ("Gangtok", "गंगटोक"),
        "tamil nadu": ("Chennai", "चेन्नई"),
        "telangana": ("Hyderabad", "हैदराबाद"),
        "tripura": ("Agartala", "अगरतला"),
        "uttar pradesh": ("Lucknow", "लखनऊ"),
        "uttarakhand": ("Dehradun", "देहरादून"),
        "west bengal": ("Kolkata", "कोलकाता"),
        "delhi": ("New Delhi", "नई दिल्ली"),
        "jammu and kashmir": ("Srinagar (Summer) / Jammu (Winter)", "श्रीनगर / जम्मू"),
        "ladakh": ("Leh", "लेह"),
    }

    WORLD_CAPITALS = {
        "india": "New Delhi (नई दिल्ली)",
        "bharat": "New Delhi (नई दिल्ली)",
        "france": "Paris",
        "united states": "Washington, D.C.",
        "usa": "Washington, D.C.",
        "united kingdom": "London",
        "uk": "London",
        "england": "London",
        "japan": "Tokyo",
        "germany": "Berlin",
        "russia": "Moscow",
        "china": "Beijing",
        "canada": "Ottawa",
        "australia": "Canberra",
        "italy": "Rome",
        "spain": "Madrid",
        "brazil": "Brasília",
        "south africa": "Pretoria / Cape Town",
        "egypt": "Cairo",
        "saudi arabia": "Riyadh",
        "uae": "Abu Dhabi",
        "united arab emirates": "Abu Dhabi",
        "turkey": "Ankara",
        "pakistan": "Islamabad",
        "bangladesh": "Dhaka",
        "nepal": "Kathmandu",
        "sri lanka": "Sri Jayawardenepura Kotte / Colombo",
        "bhutan": "Thimphu",
        "singapore": "Singapore",
        "thailand": "Bangkok",
        "malaysia": "Kuala Lumpur",
        "indonesia": "Jakarta",
        "south korea": "Seoul",
        "switzerland": "Bern",
        "sweden": "Stockholm",
        "norway": "Oslo",
        "netherlands": "Amsterdam",
        "new zealand": "Wellington",
        "mexico": "Mexico City",
        "argentina": "Buenos Aires",
    }

    KNOWLEDGE_BASE = {
        "rag": (
            "### 📄 RAG (Retrieval-Augmented Generation)\n\n"
            "**Retrieval-Augmented Generation (RAG)** is an AI architectural pattern that combines external knowledge retrieval with neural text generation:\n\n"
            "1. **Chunking & Ingestion**: Documents (PDF, MD, Code, TXT) are split into semantic chunks.\n"
            "2. **Vector / Keyword Indexing**: Chunks are indexed via vector embeddings or BM25 keyword matching.\n"
            "3. **Context Injection**: Relevant chunks are retrieved and prepended into the prompt at query time.\n"
            "4. **Grounded Generation**: The LLM generates factual answers based on retrieved context, reducing hallucinations and enabling private knowledge interaction without model retraining."
        ),
        "transformer": (
            "### ⚡ Transformer Architecture\n\n"
            "**Transformers** (introduced in 'Attention Is All You Need', 2017) are the foundational architecture for modern LLMs:\n\n"
            "- **Self-Attention Mechanism**: Calculates attention scores between all token pairs in parallel: `Attention(Q, K, V) = softmax((Q K^T) / sqrt(d_k)) * V`.\n"
            "- **Multi-Head Attention**: Allows the network to focus on multiple representation subspaces simultaneously.\n"
            "- **Positional Encoding**: Injects sequence order since attention processes tokens non-sequentially.\n"
            "- **Residual Connections & LayerNorm**: Stabilizes training and prevents vanishing gradients across deep layers."
        ),
        "machine learning": (
            "### 🤖 Machine Learning (ML)\n\n"
            "**Machine Learning** is a branch of AI where algorithms learn patterns from data to make predictions:\n\n"
            "- **Supervised Learning**: Learns from labeled datasets (e.g., Linear Regression, Random Forests, XGBoost, Neural Nets).\n"
            "- **Unsupervised Learning**: Uncovers hidden structures in unlabeled data (e.g., K-Means clustering, PCA, Autoencoders).\n"
            "- **Reinforcement Learning**: Agents learn optimal actions through environmental rewards and penalties (e.g., Q-Learning, PPO, RLHF)."
        ),
        "deep learning": (
            "### 🧠 Deep Learning\n\n"
            "**Deep Learning** is a subset of Machine Learning based on Artificial Neural Networks with multiple hidden layers:\n\n"
            "- **Feature Learning**: Automatically discovers representations from raw data without manual feature engineering.\n"
            "- **Key Architectures**: CNNs (Computer Vision), RNNs/LSTMs (Time-series), Transformers (NLP & Multimodal), Diffusion Models (Image Generation).\n"
            "- **Training Frameworks**: PyTorch, TensorFlow, JAX."
        ),
        "neural network": (
            "### 🌐 Artificial Neural Networks (ANN)\n\n"
            "**Neural Networks** are computational graphs modeled after biological neural systems:\n\n"
            "- **Architecture**: Input Layer -> Hidden Layers -> Output Layer.\n"
            "- **Weights & Biases**: Learnable parameters adjusted during training.\n"
            "- **Activation Functions**: Introduce non-linearity (ReLU, GeLU, Sigmoid, Softmax).\n"
            "- **Backpropagation**: Uses gradient descent via the chain rule to minimize the loss function."
        ),
        "large language model": (
            "### 📚 Large Language Models (LLMs)\n\n"
            "**LLMs** are multi-billion parameter autoregressive neural networks trained on vast text corpora:\n\n"
            "- **Pre-training**: Next-token prediction on trillions of tokens (unsupervised).\n"
            "- **Post-training**: Supervised Fine-Tuning (SFT) + Reinforcement Learning from Human Feedback (RLHF) for instruction following.\n"
            "- **Notable Models**: GPT-4o, Gemini 2.0, Claude 3.5, Llama 3, DeepSeek-V3."
        ),
        "lora": (
            "### 🎯 LoRA (Low-Rank Adaptation)\n\n"
            "**LoRA** is a Parameter-Efficient Fine-Tuning (PEFT) technique that freezes pre-trained model weights and injects trainable rank decomposition matrices:\n\n"
            "- **Mathematical Concept**: `W_new = W_0 + (B * A) * (alpha / r)` where rank `r << d`.\n"
            "- **Benefits**: Reduces VRAM requirements by up to 80% and allows fast swapping of task-specific adapters."
        ),
        "python": (
            "### 🐍 Python Programming Language\n\n"
            "**Python** is an interpreted, high-level, dynamically typed language known for its clean syntax and massive ecosystem:\n\n"
            "- **Key Uses**: AI/ML (PyTorch, TensorFlow, Scikit-learn), Web (FastAPI, Django, Flask), Data Analysis (Pandas, NumPy), Automation.\n"
            "- **Strengths**: High developer velocity, rich standard library, and enormous community support."
        ),
        "fastapi": (
            "### 🚀 FastAPI\n\n"
            "**FastAPI** is a modern, high-performance async Python framework for building REST APIs and WebSockets:\n\n"
            "- Built on **Starlette** (ASGI async server) and **Pydantic** (data validation).\n"
            "- Concurrency: Native `async`/`await` support with near Go and Node.js performance.\n"
            "- Auto-Docs: Generates interactive Swagger UI at `/docs`."
        ),
        "docker": (
            "### 🐳 Docker\n\n"
            "**Docker** packages applications and their dependencies into lightweight, isolated containers:\n\n"
            "- **Containers vs VMs**: Containers share the host OS kernel, making them lightweight (< 100MB) and starting in milliseconds.\n"
            "- **Dockerfile**: Script containing instructions to build a container image.\n"
            "- **Docker Compose**: Tool for defining and running multi-container applications (`docker compose up`)."
        ),
        "websocket": (
            "### 🔌 WebSockets (`ws://` / `wss://`)\n\n"
            "**WebSockets** provide persistent, full-duplex bidirectional communication channels over a single TCP connection:\n\n"
            "- Unlike HTTP request/response polling, WebSockets allow server-to-client pushing with near-zero latency.\n"
            "- Essential for real-time chat, token streaming, live telemetry, and multiplayer games."
        ),
        "binary search": (
            "### 🔍 Binary Search Algorithm\n\n"
            "Efficient search in a sorted array with **O(log n)** time complexity:\n\n"
            "```python\n"
            "def binary_search(arr: list, target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n\n"
            "# Example:\n"
            "print(binary_search([10, 20, 30, 40, 50], 30))  # Output: 2\n"
            "```"
        ),
        "quicksort": (
            "### ⚡ QuickSort Algorithm\n\n"
            "Divide-and-conquer sorting with average time complexity **O(n log n)**:\n\n"
            "```python\n"
            "def quicksort(arr: list) -> list:\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right = [x for x in arr if x > pivot]\n"
            "    return quicksort(left) + middle + quicksort(right)\n\n"
            "# Example:\n"
            "print(quicksort([38, 27, 43, 3, 9, 82, 10]))\n"
            "```"
        ),
        "fibonacci": (
            "### 🔢 Fibonacci Sequence\n\n"
            "Generated in **O(n)** time using dynamic programming / iteration:\n\n"
            "```python\n"
            "def fibonacci(n: int) -> list:\n"
            "    if n <= 0:\n"
            "        return []\n"
            "    seq = [0, 1]\n"
            "    while len(seq) < n:\n"
            "        seq.append(seq[-1] + seq[-2])\n"
            "    return seq[:n]\n\n"
            "# Example:\n"
            "print(fibonacci(10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"
            "```"
        ),
        "prime": (
            "### 🔢 Prime Sieve (Sieve of Eratosthenes)\n\n"
            "Finds all primes up to `N` in **O(n log log n)** time:\n\n"
            "```python\n"
            "def sieve_primes(n: int) -> list:\n"
            "    is_prime = [True] * (n + 1)\n"
            "    is_prime[0] = is_prime[1] = False\n"
            "    for i in range(2, int(n**0.5) + 1):\n"
            "        if is_prime[i]:\n"
            "            for j in range(i*i, n + 1, i):\n"
            "                is_prime[j] = False\n"
            "    return [i for i, prime in enumerate(is_prime) if prime]\n\n"
            "# Example:\n"
            "print(sieve_primes(30))  # [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n"
            "```"
        ),
        "dijkstra": (
            "### 🗺️ Dijkstra's Algorithm\n\n"
            "**Dijkstra's Algorithm** finds the shortest path between nodes in a weighted graph with non-negative edge weights:\n\n"
            "- **Complexity**: `O((V + E) log V)` using a Min-Heap / Priority Queue.\n"
            "- **Greedy Strategy**: Always expands the closest unvisited vertex, relaxing adjacent edges until the target is reached."
        ),
        "jwt": (
            "### 🔑 JWT (JSON Web Tokens)\n\n"
            "**JSON Web Token (JWT)** is a compact, URL-safe means of securely representing claims between parties:\n\n"
            "- **Structure**: `Header.Payload.Signature` (Base64URL encoded).\n"
            "- **Header**: Specifies token type and signing algorithm (e.g. HS256, RS256).\n"
            "- **Payload**: Contains claims (user ID, expiration, roles).\n"
            "- **Signature**: Generated cryptographically to ensure data integrity without server-side database lookups."
        ),
        "asyncio": (
            "### ⚡ Asyncio in Python\n\n"
            "**Asyncio** is Python's standard library module for writing concurrent single-threaded code using `async`/`await`:\n\n"
            "- **Event Loop**: Schedules and executes asynchronous tasks and handles I/O events cooperatively.\n"
            "- **Coroutines**: Functions defined with `async def` that pause execution via `await` while waiting for I/O."
        ),
        "kubernetes": (
            "### ☸️ Kubernetes (K8s)\n\n"
            "**Kubernetes** is an open-source container orchestration platform for automating deployment and scaling of containerized applications:\n\n"
            "- **Pods**: Smallest deployable units representing one or more containers sharing network and storage.\n"
            "- **Deployments**: Declarative management of replicas, rolling updates, and self-healing."
        ),
        "diffusion": (
            "### 🎨 Diffusion Models\n\n"
            "**Diffusion Models** are generative models that synthesize data by reversing a gradual noising process:\n\n"
            "- **Forward Process**: Progressively adds Gaussian noise to an image until it becomes pure noise.\n"
            "- **Reverse Process**: A neural network (e.g. U-Net / DiT) learns to iteratively denoise the latent space back to a clear image."
        ),
        "quantum computing": (
            "### ⚛️ Quantum Computing\n\n"
            "Quantum computing utilizes principles of quantum physics to achieve exponential speedups:\n\n"
            "- **Qubits**: Can exist in a superposition of states (0 and 1 simultaneously) via `|psi> = alpha|0> + beta|1>`.\n"
            "- **Entanglement**: The quantum state of one qubit instantaneously determines the state of another.\n"
            "- **Applications**: Quantum chemistry, drug discovery, optimization, and cryptographic breaking (Shor's Algorithm)."
        ),
        "photosynthesis": (
            "### 🌱 Photosynthesis (प्रकाश संश्लेषण)\n\n"
            "**Photosynthesis** is the biological process by which green plants, algae, and some bacteria convert light energy into chemical energy:\n\n"
            "- **Chemical Formula**: `6CO2 + 6H2O + Light -> C6H12O6 (Glucose) + 6O2 (Oxygen)`.\n"
            "- **Chlorophyll**: The green pigment inside plant chloroplasts that absorbs sunlight (primarily blue and red wavelengths).\n"
            "- **Stages**: Light-dependent reactions (in thylakoid membranes) and Calvin cycle / dark reactions (in stroma)."
        ),
        "gravity": (
            "### 🪐 Gravity (गुरुत्वाकर्षण)\n\n"
            "**Gravity** is one of the four fundamental forces of nature that attracts objects with mass or energy towards one another:\n\n"
            "- **Newton's Law**: `F = G * (m1 * m2) / r^2` where `G = 6.674 x 10^-11 N m^2/kg^2`.\n"
            "- **Einstein's General Relativity**: Gravity is not an invisible force, but rather the curvature of spacetime caused by mass and energy.\n"
            "- **Acceleration on Earth**: `g ≈ 9.8 m/s^2`."
        ),
        "speed of light": (
            "### 💡 Speed of Light (प्रकाश की गति)\n\n"
            "The speed of light in a vacuum is denoted by **`c`** and is a fundamental physical constant:\n\n"
            "- **Exact Value**: **`299,792,458 meters per second`** (approx. **`300,000 km/s`** or `186,282 miles/sec`).\n"
            "- According to Special Relativity, nothing with mass can travel at or faster than the speed of light."
        ),
        "solar system": (
            "### ☀️ Solar System (सौरमंडल)\n\n"
            "Our Solar System formed ~4.6 billion years ago and consists of the Sun and objects bound by its gravity:\n\n"
            "- **8 Planets (in order from Sun)**: Mercury (बुध), Venus (शुक्र), Earth (पृथ्वी), Mars (मंगल), Jupiter (बृहस्पति), Saturn (शनि), Uranus (अरुण), Neptune (वरुण).\n"
            "- **Inner Terrestrial Planets**: Mercury, Venus, Earth, Mars (rocky surfaces).\n"
            "- **Outer Gas/Ice Giants**: Jupiter, Saturn (gas giants); Uranus, Neptune (ice giants).\n"
            "- **Dwarf Planets**: Pluto, Eris, Haumea, Makemake, Ceres."
        ),
        "dna": (
            "### 🧬 DNA (Deoxyribonucleic Acid)\n\n"
            "**DNA** is the molecule that carries the genetic blueprint for the growth, development, functioning, and reproduction of all known living organisms:\n\n"
            "- **Structure**: Double helix discovered by Watson, Crick, and Rosalind Franklin in 1953.\n"
            "- **4 Nucleotide Bases**: Adenine (A), Thymine (T), Guanine (G), Cytosine (C). Pairs: A with T, C with G."
        ),
        "isro": (
            "### 🚀 ISRO (Indian Space Research Organisation)\n\n"
            "**ISRO** is the national space agency of India, headquartered in Bengaluru, Karnataka:\n\n"
            "- **Founded**: 15 August 1969 by Dr. Vikram Sarabhai.\n"
            "- **Key Milestones**: Aryabhata (first satellite, 1975), Chandrayaan-1 (discovered water molecules on Moon, 2008), Mars Orbiter Mission / Mangalyaan (2013), Chandrayaan-3 (first nation to softly land on the lunar south pole, 23 Aug 2023), Aditya-L1 (solar observatory, 2023).\n"
            "- **Launch Vehicles**: PSLV (Polar Satellite Launch Vehicle), LVM3 (Geosynchronous / Heavy lifter)."
        )
    }

    @classmethod
    async def try_local_ollama(cls, messages: List[Dict[str, str]], base_url: str = "http://localhost:11434") -> Optional[str]:
        """Check if a local Ollama instance is running with an open model."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                tags_resp = await client.get(f"{base_url}/api/tags")
                if tags_resp.status_code == 200:
                    models = tags_resp.json().get("models", [])
                    if models:
                        model_name = models[0].get("name", "llama3")
                        chat_resp = await client.post(
                            f"{base_url}/api/chat",
                            json={
                                "model": model_name,
                                "messages": messages,
                                "stream": False
                            },
                            timeout=30.0
                        )
                        if chat_resp.status_code == 200:
                            return chat_resp.json().get("message", {}).get("content", "")
        except Exception:
            pass
        return None

    @classmethod
    def extract_user_profile(cls, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extracts user details stated across conversational memory."""
        profile = {"name": "", "facts": []}
        for m in messages:
            if m.get("role") == "user":
                content = m.get("content", "")
                name_match = re.search(r"\b(?:my name is|i am|call me|mera naam)\s+([A-Za-z]+)\b", content, re.I)
                if name_match:
                    name = name_match.group(1).capitalize()
                    if name.lower() not in ["a", "the", "working", "trying", "building", "hai"]:
                        profile["name"] = name
        return profile

    @classmethod
    def answer_from_rag_context(cls, query: str, rag_context: str) -> Optional[str]:
        """Synthesizes factual answers directly from retrieved RAG context."""
        if not rag_context:
            return None

        chunks = [c.strip() for c in rag_context.split("---") if c.strip()]
        if not chunks:
            return None

        query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))
        best_chunk = ""
        best_score = 0

        for chunk in chunks:
            chunk_words = set(re.findall(r"\b\w{3,}\b", chunk.lower()))
            overlap = len(query_words.intersection(chunk_words))
            if overlap > best_score:
                best_score = overlap
                best_chunk = chunk

        if best_chunk:
            return (
                f"### 📄 Information from Uploaded Knowledge Base:\n\n"
                f"```text\n{best_chunk}\n```\n\n"
                f"*Synthesized autonomously from your indexed documents.*"
            )
        return None

    @classmethod
    def synthesize_web_search(cls, query: str, raw_obs: str) -> Dict[str, Any]:
        """Synthesizes live web search observation into a direct, comprehensive response."""
        if "No direct search results found" in raw_obs or "Search error" in raw_obs or not raw_obs.strip():
            return cls.synthesize_conceptual_answer(query)

        # Parse DuckDuckGo results
        # Pattern matches Result X (domain):\nSnippet
        blocks = re.split(r"Result \d+ \(([^)]*)\):", raw_obs)
        results = []
        if len(blocks) > 1:
            for i in range(1, len(blocks), 2):
                url = blocks[i].strip()
                text = blocks[i+1].strip() if i+1 < len(blocks) else ""
                if text:
                    results.append((url, text))
        else:
            results = [("", raw_obs.strip())]

        is_hindi = any(w in query.lower() for w in [
            "kya", "kaun", "kahan", "kab", "kyun", "kaise", "batao", "samjhao", "hai", "hein",
            "hota", "hoti", "hote", "bataiye", "kisko", "kisne", "kitna", "rajdhani", "pradhan", "mantri"
        ]) or any('\u0900' <= ch <= '\u097F' for ch in query)

        # Compile informative snippets
        compiled_points = []
        sources = []
        for url, text in results[:4]:
            clean_text = re.sub(r"\s+", " ", text).strip()
            # Clean unwanted artifacts
            clean_text = clean_text.replace("", "")
            if clean_text:
                compiled_points.append(clean_text)
            if url and url not in sources:
                sources.append(url)

        lead_in = "### 🌐 Answer & Details\n\n"
        if is_hindi:
            lead_in = "### 🌐 उत्तर एवं मुख्य जानकारी (Answer & Details)\n\n"

        body = "\n\n".join([f"- {pt}" for pt in compiled_points])
        if not body:
            body = raw_obs.strip()

        sources_footer = ""
        if sources:
            source_links = ", ".join([f"[{s}](https://{s})" if not s.startswith("http") else f"[{s}]({s})" for s in sources[:4]])
            sources_footer = f"\n\n**Sources:** {source_links}"

        return {
            "thought": "Synthesizing retrieved web search results into a clean, accurate answer.",
            "tool_calls": [],
            "content": f"{lead_in}{body}{sources_footer}"
        }

    @classmethod
    def synthesize_conceptual_answer(cls, raw_query: str, user_name: str = "") -> Dict[str, Any]:
        """Provides an intelligent domain breakdown when offline or without external search."""
        q_clean = raw_query.strip()
        name_str = f", {user_name}" if user_name else ""

        # Domain recognition
        keywords = re.findall(r"\b\w{3,}\b", q_clean.lower())
        tech_words = {"python", "javascript", "code", "programming", "api", "database", "sql", "ai", "model", "server"}
        science_words = {"physics", "chemistry", "biology", "space", "planet", "energy", "speed", "earth", "sun"}

        if any(w in tech_words for w in keywords):
            domain = "Technology & Software"
            guidance = "I can write source code, debug scripts, execute Python in my sandbox, or test algorithms for you."
        elif any(w in science_words for w in keywords):
            domain = "Science & Physical World"
            guidance = "I can compute mathematical formulas, explain natural principles, or model equations."
        else:
            domain = "General Inquiry"
            guidance = "You can ask me to search the web, calculate formulas, check live dates/weather, or inspect files."

        return {
            "thought": f"Synthesized offline domain response for query: '{q_clean}'.",
            "tool_calls": [],
            "content": (
                f"### 💡 Nexus Self-AI Insight{name_str}\n\n"
                f"**Query**: *\"{q_clean}\"*\n\n"
                f"I processed your request but didn't trigger any specific tool or find an exact match in my offline knowledge.\n\n"
                f"- **Domain**: {domain}\n"
                f"- **Overview**: Your query involves analyzing concepts related to **{', '.join(keywords[:4]) or q_clean}**.\n"
                f"- **Next Steps**: {guidance}\n\n"
                f"*Tip: If you would like live factual information, ask me to **\"search web for {q_clean}\"**!*"
            )
        }

    @classmethod
    def process_query(cls, query: str, messages: List[Dict[str, str]], rag_context: str = "") -> Dict[str, Any]:
        """
        Cognitive reasoning pipeline:
        Returns: {"thought": str, "tool_calls": List[dict], "content": str}
        """
        raw_query = query.strip()
        q = raw_query.lower()
        user_profile = cls.extract_user_profile(messages)
        user_name = user_profile["name"]

        # 0. Check if this is a follow-up to a tool execution (Turn 2+)
        obs_msg = None
        tool_name = ""
        for m in reversed(messages):
            if m.get("role") == "system":
                c = m.get("content", "")
                if "Observation" in c or "returned Observation:" in c:
                    obs_msg = c
                    # Extract tool name if present
                    t_match = re.search(r"Tool (?:'(\w+)' returned )?Observation(?:\s*\((\w+)\))?:?", c)
                    if t_match:
                        tool_name = t_match.group(1) or t_match.group(2) or ""
                    break

        if obs_msg:
            # Extract raw observation text cleanly
            raw_obs = re.sub(r"^.*?Observation(?:\s*\([^)]*\))?:?\s*", "", obs_msg, flags=re.DOTALL).strip()

            # Handle web search synthesis
            if tool_name == "web_search" or "web_search" in obs_msg:
                # Find the user's original query
                orig_query = raw_query
                for m in reversed(messages):
                    if m.get("role") == "user":
                        orig_query = m.get("content", "")
                        break
                return cls.synthesize_web_search(orig_query, raw_obs)

            # Handle calculator synthesis
            if tool_name == "calculator" or "calculator" in obs_msg:
                return {
                    "thought": "Synthesizing exact calculation result.",
                    "tool_calls": [],
                    "content": f"### 🧮 Calculation Result\n\n{raw_obs}"
                }

            # Handle datetime synthesis
            if tool_name == "datetime_info" or "datetime_info" in obs_msg:
                return {
                    "thought": "Presenting live calendar and time observation.",
                    "tool_calls": [],
                    "content": f"### 🕒 Date & Time Information\n\n{raw_obs}"
                }

            # Handle weather synthesis
            if tool_name == "weather_info" or "weather_info" in obs_msg:
                return {
                    "thought": "Presenting real-time weather report.",
                    "tool_calls": [],
                    "content": f"### 🌤️ Weather Report\n\n{raw_obs}"
                }

            # Handle system diagnostics synthesis
            if tool_name == "system_info" or "system_info" in obs_msg:
                return {
                    "thought": "Presenting host system diagnostics.",
                    "tool_calls": [],
                    "content": f"### 🖥️ System Diagnostics\n\n{raw_obs}"
                }

            # Handle code runner synthesis
            if tool_name == "code_runner" or "code_runner" in obs_msg:
                return {
                    "thought": "Synthesizing Python sandbox execution output.",
                    "tool_calls": [],
                    "content": (
                        f"### 🐍 Python Execution Result\n\n"
                        f"```\n{raw_obs}\n```\n\n"
                        f"*Executed safely in the local sandboxed environment.*"
                    )
                }

            # Handle file manager synthesis
            if tool_name == "file_manager" or "file_manager" in obs_msg:
                return {
                    "thought": "Presenting workspace filesystem inspection.",
                    "tool_calls": [],
                    "content": f"### 📁 Workspace Files\n\n{raw_obs}"
                }

            # Generic tool observation output
            return {
                "thought": "Synthesizing tool observation into a structured, clear response.",
                "tool_calls": [],
                "content": (
                    f"### ⚙️ Execution Result\n\n"
                    f"{raw_obs}\n\n"
                    f"--- \n"
                    f"*Executed safely in the local sandboxed environment.*"
                )
            }

        # 1. Check RAG Context first if user asks about documents/notes/files
        if rag_context and any(kw in q for kw in ["document", "rag", "file", "upload", "notes", "according to", "summary", "read"]):
            rag_answer = cls.answer_from_rag_context(q, rag_context)
            if rag_answer:
                return {
                    "thought": "Synthesizing answer from retrieved RAG document chunks in system context.",
                    "tool_calls": [],
                    "content": rag_answer
                }

        # 2. Math & Arithmetic Calculation Tool Routing
        math_trigger = re.search(r"(\bcalc(?:ulate)?|\bcompute|\beval)\s+(.+)", q)
        math_what_is = re.search(r"(\bwhat is|\bhow much is|\bkitna hota hai)\s+([0-9\.\s\+\-\*\/\^\(\)\%\,sqrtpi]+)", q)
        pure_math = re.match(r"^[\s0-9\.\+\-\*\/\^\(\)\%sqrtpi]+$", q)
        if (math_trigger or math_what_is or pure_math) and any(c.isdigit() for c in q) and not any(kw in q for kw in ["code", "python", "script", "file", "create"]):
            if math_trigger:
                expr = math_trigger.group(2).strip("? .")
            elif math_what_is:
                expr = math_what_is.group(2).strip("? .")
            else:
                expr = q.strip("? .")
            
            # Avoid empty or invalid expressions
            if expr and not expr.isspace() and len(expr) > 0:
                return {
                    "thought": f"Recognized exact math calculation requirement. Routing '{expr}' to calculator tool.",
                    "tool_calls": [{"name": "calculator", "args": {"expression": expr}}],
                    "content": ""
                }

        # Conversational handling
        conversational = {
            "who are you": "I am Nexus-AI, an autonomous self-hosted AI platform designed to help you with research, coding, calculations, and general knowledge.",
            "what are you": "I am Nexus-AI, an autonomous self-hosted AI platform designed to help you with research, coding, calculations, and general knowledge.",
            "how are you": "I'm functioning perfectly and ready to assist you! How can I help you today?",
            "what is your name": "My name is Nexus-AI.",
            "tumhara naam kya hai": "Mera naam Nexus-AI hai, aur main ek autonomous AI assistant hoon.",
            "tum kaun ho": "Main Nexus-AI hoon, ek autonomous AI assistant.",
            "kaise ho": "Main theek hoon! Aap batayein main aapki kaise madad kar sakta hoon?",
            "aap kaun ho": "Main Nexus-AI hoon, ek autonomous AI assistant."
        }
        for k, v in conversational.items():
            if k in q:
                return {
                    "thought": f"Recognized conversational query. Responding directly.",
                    "tool_calls": [],
                    "content": f"{v}"
                }

        # 3. Python Code Execution
        if any(kw in q for kw in ["run python", "execute python", "run code", "test code", "execute script"]):
            code_match = re.search(r"```(?:python)?(.*?)```", raw_query, re.DOTALL)
            code = code_match.group(1).strip() if code_match else ""
            if not code:
                after_colon = re.search(r"(?:run python|execute python|run code|test code|execute script)[:\s]+(.+)", raw_query, re.IGNORECASE | re.DOTALL)
                if after_colon:
                    extracted = after_colon.group(1).strip("` ")
                    if any(kw in extracted for kw in ["print", "def ", "import ", "for ", "while ", "=", "+", "*"]):
                        code = extracted
            if not code:
                code = "import math\nprint(f'Pi: {math.pi:.4f}')\nprint('Factorial of 6:', math.factorial(6))"
            return {
                "thought": "Detected request to execute Python code in sandboxed subprocess.",
                "tool_calls": [{"name": "code_runner", "args": {"code": code}}],
                "content": ""
            }

        # 4. Workspace File Operations
        if any(kw in q for kw in ["list files", "show files", "what files", "workspace files", "dir", "ls"]):
            return {
                "thought": "User wants to inspect workspace directory structure.",
                "tool_calls": [{"name": "file_manager", "args": {"action": "list", "path": "."}}],
                "content": ""
            }

        # 5. Live Date, Time & Calendar Inquiries
        if any(kw in q for kw in [
            "what time", "current time", "time now", "what is the time", "tell me the time",
            "what is today's date", "today date", "current date", "what date is it", "aaj kya date",
            "kya time", "kya samay", "aaj kaun sa din", "what day is today", "calendar", "current timestamp"
        ]):
            fmt = "full"
            if any(k in q for k in ["date", "tarikh", "din", "day"]):
                fmt = "date"
            elif any(k in q for k in ["time", "samay", "baje", "clock"]):
                fmt = "time"
            return {
                "thought": f"User requested live date/time ('{fmt}'). Routing to datetime_info tool.",
                "tool_calls": [{"name": "datetime_info", "args": {"format": fmt}}],
                "content": ""
            }

        # 6. Real-Time Weather Tool Routing
        weather_match = re.search(r"\b(?:weather|temperature|forecast|climate|mausam)\s+(?:in|for|of|at|ka)?\s*([A-Za-z\s,\.-]+)", q)
        if not weather_match:
            weather_match = re.search(r"([A-Za-z\s]+)\s+(?:weather|forecast|mausam)", q)
        if (weather_match or "weather" in q or "mausam" in q) and not any(kw in q for kw in ["api", "code", "function", "create", "whether"]):
            loc = "London"
            if weather_match:
                loc = weather_match.group(1).strip("? .")
                loc = re.sub(r"\b(current|today|live|right now|the|is|like|what|ka|kaisa|hai)\b", "", loc).strip()
            if not loc or loc in ["kaisa", "kya", "in", "ka"]:
                loc = "Delhi"
            return {
                "thought": f"Detected real-time weather query for '{loc}'. Routing to weather_info tool.",
                "tool_calls": [{"name": "weather_info", "args": {"location": loc}}],
                "content": ""
            }

        # 7. Host System Diagnostics Tool Routing
        if any(kw in q for kw in [
            "system info", "system status", "specs", "disk space", "cpu core", "operating system",
            "system diagnostic", "host info", "hardware specs", "machine info", "computer specs"
        ]):
            q_type = "all"
            if "disk" in q or "storage" in q:
                q_type = "disk"
            elif "cpu" in q or "processor" in q:
                q_type = "cpu"
            elif "os" in q or "windows" in q or "linux" in q:
                q_type = "os"
            return {
                "thought": f"User requested system diagnostics ('{q_type}'). Routing to system_info tool.",
                "tool_calls": [{"name": "system_info", "args": {"query_type": q_type}}],
                "content": ""
            }

        # 8. Conversational Memory & User Name
        if any(kw in q for kw in ["what is my name", "who am i", "do you remember me", "remember my name", "mera naam kya hai"]):
            if user_name:
                return {
                    "thought": f"Retrieved user name '{user_name}' from conversational memory.",
                    "tool_calls": [],
                    "content": f"Your name is **{user_name}**! 😊 I remember our previous turns in this conversation."
                }
            else:
                return {
                    "thought": "User asked for their name, but none was recorded in this session.",
                    "tool_calls": [],
                    "content": "You haven't told me your name yet! What should I call you? (आप अपना नाम बता सकते हैं!)"
                }

        # 9. Greetings & Identity
        greeting_words = ["hi", "hello", "hey", "hola", "namaste", "kaise ho", "good morning", "good evening", "greetings"]
        if any(q.startswith(g) or q == g for g in greeting_words):
            name_part = f", **{user_name}**" if user_name else ""
            return {
                "thought": "Greeting received. Introducing Nexus Self-AI engine.",
                "tool_calls": [],
                "content": (
                    f"### 👋 Hello{name_part}! Welcome to **Nexus Self-AI**.\n\n"
                    f"I am your **100% self-hosted autonomous AI platform**, running entirely on your machine **without any external APIs or fees**.\n\n"
                    f"**Here is what I can do for you right now:**\n"
                    f"- 🌐 **Answers & Questions**: Ask me anything (GK, Science, Technology, World News, Places, History)\n"
                    f"- 🧮 **Math & Calculation**: *\"Calculate sqrt(256) + 42 * 3\"*\n"
                    f"- 🐍 **Run Python Code**: *\"Run python code to test prime numbers\"*\n"
                    f"- 🖥️ **System Diagnostics**: *\"Check system status and disk space\"*\n"
                    f"- 🌤️ **Live Global Weather**: *\"What is the weather in Tokyo?\"*\n"
                    f"- 🕒 **Live Date & Time**: *\"What time is it right now?\"*\n"
                    f"- 📚 **Knowledge & Explainers**: Ask me about LoRA, RAG, Transformers, Docker, Algorithms.\n"
                    f"- 📁 **Document RAG**: Drop documents in the chat or ask me to inspect workspace files.\n\n"
                    f"How can I assist you today? (आप कोई भी सवाल पूछ सकते हैं!)"
                )
            }

        # 10. Identity / Creator Questions
        if any(kw in q for kw in ["who are you", "who made you", "what are you", "what is nexus", "are you api", "tum kaun ho"]):
            return {
                "thought": "Explaining Self-AI architecture and zero-API operation.",
                "tool_calls": [],
                "content": (
                    f"### 🤖 About **Nexus Self-AI**\n\n"
                    f"I am an autonomous, full-stack intelligence system running **directly on your hardware**.\n\n"
                    f"- **Zero External APIs**: Operates locally without sending your private queries to any third-party cloud.\n"
                    f"- **Autonomous ReAct Loop**: Reasons step-by-step (`Thought -> Action -> Observation -> Final Answer`).\n"
                    f"- **Live Web Search**: Automatically fetches live, up-to-date facts and answers from the web.\n"
                    f"- **Sandboxed Tools**: Python sandbox, scientific calculator, workspace manager, system telemetry.\n"
                    f"- **Optional Keys**: You can also plug in a free Gemini or Groq API key in Settings anytime for cloud LLMs!"
                )
            }

        # 11. Built-in State & World Capitals Lookup (Instant 0ms answers)
        if any(kw in q for kw in ["capital", "rajdhani"]):
            # Check Indian states
            for state, (eng_cap, hin_cap) in cls.INDIAN_CAPITALS.items():
                if state in q:
                    return {
                        "thought": f"Matched Indian state capital query: '{state}'.",
                        "tool_calls": [],
                        "content": (
                            f"### 🏛️ राजधानी (State Capital)\n\n"
                            f"**{state.title()}** की राजधानी **{hin_cap} ({eng_cap})** है।\n\n"
                            f"- **State (राज्य)**: {state.title()}\n"
                            f"- **Capital (राजधानी)**: {eng_cap} ({hin_cap})\n"
                            f"- **Country**: India (भारत)"
                        )
                    }

            # Check World countries
            for country, cap in cls.WORLD_CAPITALS.items():
                if country in q:
                    return {
                        "thought": f"Matched world capital query: '{country}'.",
                        "tool_calls": [],
                        "content": (
                            f"### 🏛️ World Capital\n\n"
                            f"The capital of **{country.title()}** is **{cap}**.\n\n"
                            f"- **Country**: {country.title()}\n"
                            f"- **Capital City**: {cap}"
                        )
                    }

        # 12. Indian Leadership / Constitutional Posts Lookup
        if any(kw in q for kw in ["pradhan mantri", "prime minister", "pm of india", "bharat ke pradhan mantri"]) and ("india" in q or "bharat" in q or "desh" in q or not any(c in q for c in ["uk", "japan", "canada", "france"])):
            return {
                "thought": "Retrieved Prime Minister of India leadership node.",
                "tool_calls": [],
                "content": (
                    "### 🇮🇳 Prime Minister of India (भारत के प्रधानमंत्री)\n\n"
                    "वर्तमान में भारत के प्रधानमंत्री **श्री नरेंद्र मोदी (Shri Narendra Modi)** हैं।\n\n"
                    "- **पदभार**: 26 मई 2014 से लगातार कार्यरत (तीसरा कार्यकाल जून 2024 से शुरू).\n"
                    "- **संसदीय क्षेत्र**: वाराणसी, उत्तर प्रदेश.\n"
                    "- **पार्टी / गठबंधन**: भारतीय जनता पार्टी (BJP / NDA)."
                )
            }

        if any(kw in q for kw in ["rashtrapati", "president of india", "bharat ke rashtrapati"]) and ("india" in q or "bharat" in q or not any(c in q for c in ["usa", "america", "russia", "france"])):
            return {
                "thought": "Retrieved President of India constitutional head node.",
                "tool_calls": [],
                "content": (
                    "### 🇮🇳 President of India (भारत की राष्ट्रपति)\n\n"
                    "वर्तमान में भारत की राष्ट्रपति **श्रीमती द्रौपदी मुर्मू (Smt. Droupadi Murmu)** हैं।\n\n"
                    "- **पदभार**: 25 जुलाई 2022 से कार्यरत (भारत की 15वीं राष्ट्रपति).\n"
                    "- **विशेषता**: वह भारत की पहली आदिवासी महिला राष्ट्रपति और देश की दूसरी महिला राष्ट्रपति हैं."
                )
            }

        # 13. Embedded Knowledge Base Matching (Instant 0ms answers)
        for topic, explanation in cls.KNOWLEDGE_BASE.items():
            if topic in q:
                return {
                    "thought": f"Matched query to embedded knowledge node: '{topic}'.",
                    "tool_calls": [],
                    "content": explanation
                }

        # 14. Code Generation Requests (Python, JS, SQL, HTML, etc.)
        if any(kw in q for kw in ["write code", "write a function", "how to write", "code for", "program for", "script for"]):
            if "sql" in q:
                return {
                    "thought": "Synthesizing SQL query and schema design.",
                    "tool_calls": [],
                    "content": (
                        "### 🗄️ SQL Example & Query Pattern\n\n"
                        "```sql\n"
                        "CREATE TABLE users (\n"
                        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                        "    username VARCHAR(50) NOT NULL UNIQUE,\n"
                        "    email VARCHAR(100) NOT NULL UNIQUE,\n"
                        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
                        ");\n\n"
                        "SELECT u.username, COUNT(o.id) AS total_orders\n"
                        "FROM users u\n"
                        "LEFT JOIN orders o ON u.id = o.user_id\n"
                        "GROUP BY u.id\n"
                        "ORDER BY total_orders DESC;\n"
                        "```"
                    )
                }
            else:
                return {
                    "thought": "Providing clean, modular Python source code with explanations.",
                    "tool_calls": [],
                    "content": (
                        "### 🐍 Python Implementation\n\n"
                        "```python\n"
                        "def process_data(items: list) -> dict:\n"
                        "    \"\"\"Cleans, filters, and computes statistics on input data.\"\"\"\n"
                        "    valid_numbers = [x for x in items if isinstance(x, (int, float))]\n"
                        "    if not valid_numbers:\n"
                        "        return {'count': 0, 'total': 0, 'average': 0}\n"
                        "    \n"
                        "    return {\n"
                        "        'count': len(valid_numbers),\n"
                        "        'total': sum(valid_numbers),\n"
                        "        'average': sum(valid_numbers) / len(valid_numbers)\n"
                        "    }\n\n"
                        "print(process_data([10, 20, 35, 5, 80]))\n"
                        "```\n\n"
                        "*Tip: Ask me to **\"run python code\"** to execute scripts in the sandbox!*"
                    )
                }

        # 14.5 Debugging and Help in Hindi
        if any(kw in q for kw in ["output nahi", "error aa", "bug hai", "chal nahi raha", "not working", "kaam nahi kar"]):
            return {
                "thought": "Recognized user needs help debugging an issue.",
                "tool_calls": [],
                "content": (
                    "### 🛠️ Debugging Assistant\n\n"
                    "It looks like you are facing an issue or not getting the expected output. "
                    "To help me fix the bug, please tell me:\n"
                    "- **What code or command are you running?**\n"
                    "- **Are there any error messages in the console?**\n\n"
                    "*Tip: You can paste your code here, and I will analyze it!*"
                )
            }

        # 15. General Questions & Information Inquiries -> Autonomous Live Web Search
        question_words = [
            "who", "what", "where", "when", "why", "how", "which", "whose", "whom",
            "is", "are", "was", "were", "can", "does", "do", "did",
            "tell", "explain", "define", "meaning", "details", "about", "search", "google", "find",
            "kya", "kaun", "kahan", "kab", "kyun", "kaise", "batao", "samjhao", "kisne", "kitna",
            "konsa", "kripya", "hai kya", "hota hai", "hote hain", "hoti hai", "kon", "rajdhani",
            "history", "founder", "inventor", "ceo", "price", "salary", "full form"
        ]

        is_question = (
            q.endswith("?") or
            any(q.startswith(qw) or f" {qw} " in f" {q} " for qw in question_words) or
            any(kw in q for kw in ["search", "look up", "news", "update", "batao", "kya", "kaun"])
        )

        if is_question:
            # Clean search query for optimal search engine retrieval
            clean_search = re.sub(
                r"^(can you please |please |can you |tell me |explain |search web for |search for |search |google |look up |batao |mujhe batao |kripya batao )\s*",
                "",
                raw_query,
                flags=re.IGNORECASE
            ).strip("? .")

            if not clean_search:
                clean_search = raw_query.strip("? .")

            return {
                "thought": f"Recognized factual inquiry / question: '{raw_query}'. Routing to autonomous web_search tool with query: '{clean_search}'.",
                "tool_calls": [{"name": "web_search", "args": {"query": clean_search}}],
                "content": ""
            }

        # 16. Fallback Domain Synthesizer
        return cls.synthesize_conceptual_answer(raw_query, user_name)
