import gradio as gr
from dotenv import load_dotenv
from prompts import context
#from note_engine import note_engine
import llama_index
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.llms.openai import OpenAI
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from pymilvus import connections
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.embed_model = embed_model

load_dotenv()

import logging
import sys

logging.basicConfig(stream=sys.stderr)
llama_index.core.set_global_handler("simple")

try:
    vector_store_books = MilvusVectorStore(dim=384, uri="http://milvusdb:19530", collection_name="books")
    storage_context = StorageContext.from_defaults(
        persist_dir="./storage/books",
        vector_store=vector_store_books,
    )
    books_index = load_index_from_storage(storage_context)
except Exception as error:
    print(f'Unable to load index from storage: {error}')
    print('Indexing book dataset')
    vector_store_books = MilvusVectorStore(dim=384, collection_name="books", uri="http://milvusdb:19530", overwrite=True)
    book_docs = SimpleDirectoryReader(input_dir="./data").load_data()
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store_books,
    )
    books_index = VectorStoreIndex.from_documents(book_docs, storage_context=storage_context)
    books_index.storage_context.persist(persist_dir="./storage/books")

books_query_engine = books_index.as_query_engine(similarity_top_k=3)

tools = [
    QueryEngineTool(
        query_engine=books_query_engine,
        metadata=ToolMetadata(
            name="books_data",
            description="Provides information about known books; ONLY books known to this tool should be considered when answering questions about books",
        ),
    ),
]

# # This is the main agent
llm = OpenAI(model="gpt-3.5-turbo-0613")
agent = ReActAgent.from_tools(tools, llm=llm, verbose=True, context=context)


# UI for demo
def chat_interface(prompt):
    # Send the prompt to the agent and get the response
    response = agent.query(prompt)
    print(response)
    return response

iface = gr.Interface(fn=chat_interface, 
                     inputs="text", 
                     outputs="text",
                     allow_flagging="never")

iface.launch(share=True)
