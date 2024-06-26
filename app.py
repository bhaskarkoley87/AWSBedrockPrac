import json
import os
import sys
import boto3
import streamlit as st

from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock

# Data Ingestion
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFDirectoryLoader


# Vector Embedding And Vector Store
from langchain.vectorstores import FAISS
## LLM Models
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

## Bedrock CLients
bedrock = boto3.client(service_name="bedrock-runtime", region_name='us-west-2')
bedrock_embeddings =BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock)

## Data Ingestion
def data_ingestion():
    loader=PyPDFDirectoryLoader("data")
    document=loader.load()

    # - in our
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)

    docs=text_splitter.split_documents(document)
    return docs

## Vector Embedding
def get_vector_store(docs):
    vectorstore_faiss=FAISS.from_documents(docs, bedrock_embeddings)

    vectorstore_faiss.save_local("faiss_index")

def get_AI21_llm():
    llm=Bedrock(model_id="ai21.j2-mid-v1", client=bedrock, model_kwargs={'maxTokens': 8191})

    return llm

def get_Llama2_llm():
    llm = Bedrock(model_id="meta.llama3-70b-instruct-v1:0", client=bedrock, model_kwargs={'max_gen_len': 2048})

    return llm


prompt_template = """

Human: Use the following pieces of context to provide a 
concise answer to the question at the end but use atleast summarize with 
250 words with detailed explanations. If you don't know the answer, 
just say that you don't know, don't try to make up an answer.
<context>
{context}
</context

Question: {question}

Assistant:"""

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)


def get_response_llm(llm, vectorstore_faiss, query):
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore_faiss.as_retriever(
            search_type="similarity", search_kwargs={"k": 3}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    answer = qa({"query": query})
    return answer['result']


def main():
    st.set_page_config("Chat PDF")

    st.header("Chat with PDF using AWS Bedrock💁")

    user_question = st.text_input("Ask a Question from the PDF Files")

    with st.sidebar:
        st.title("Update Or Create Vector Store:")

        if st.button("Vectors Update"):
            with st.spinner("Processing..."):
                docs = data_ingestion()
                get_vector_store(docs)
                st.success("Done")

    if st.button("AI21 Output"):
        with st.spinner("Processing..."):
            faiss_index = FAISS.load_local("faiss_index", bedrock_embeddings, allow_dangerous_deserialization=True)
            llm = get_AI21_llm()

            # faiss_index = get_vector_store(docs)
            st.write(get_response_llm(llm, faiss_index, user_question))
            st.success("Done")

    if st.button("Llama2 Output"):
        with st.spinner("Processing..."):
            faiss_index = FAISS.load_local("faiss_index", bedrock_embeddings, allow_dangerous_deserialization=True)
            llm = get_Llama2_llm()

            # faiss_index = get_vector_store(docs)
            st.write(get_response_llm(llm, faiss_index, user_question))
            st.success("Done")


if __name__ == "__main__":
    main()



