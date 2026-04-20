# NeuralDoc Search

An advanced, serverless semantic search and question-answering architecture natively tailored for your documents. 

NeuralDoc Search relies purely on local processing infrastructure rather than exposing your documents to bloated Vector Databases like Weaviate.

### Key Innovations
- **Sparse Matrix Indexing**: Native document mapping inside memory mapping.
- **Semantic Optimizer**: Local re-ranking via `cross-encoder` models to find precision hits instantly.
- **Inference Engine**: Driven by cloud compute layers.

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Author
Designed and built by _Abhijeet Abhi_ for scalable, zero-infrastructure parsing models.
