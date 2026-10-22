## Configuration

**Download Conda virtual environment**
```bash
# Create a new conda environment from environemnt file
conda env create -f environment.yml

# activate conda venv
conda activate ds-steam-game

# Run jupyter notebook
jupyter notebook
```

```bash
# Run docker and detach
docker compose up -d

# Pull requirement models
docker exec ollama ollama pull nomic-embed-text-v2-moe qwen3.5:2b
```

**Preprocess:**  
*Note*: It is **not recommneded** to run this in the pipeline entirely because the total it consumes is **about 6-10 hours of waiting**. Instead, you should use and cleaned version after 2 first processes in **021_preprocess1_crawler.ipynb** and **022_preprocess1_vectordb.ipynb**. The **chroma-data**( because the **vector database the project used is chromadb**), will be provided separately so you can download it and **try retrieval process**

- Craw for missing value: Run **021_preprocess1_crawler.ipynb** with fallback using LLM model to fill out missing value that failed to crawl  

- Vector database embbed and retrieval: Run **022_preprocess2_vectordb.ipynb**

- Normalize and Impute can be found in **023_preprocess1_norm_impu.ipynb**

