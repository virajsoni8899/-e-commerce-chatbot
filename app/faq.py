import os
import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

faqs_path = Path(__file__).parent / "resources/flipkart_faqs.csv"
chroma_client = chromadb.Client()
collections_name_faq = 'faqs'
groq_client = Groq()

ef = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def ingest_faq_data(path):
    if collections_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print("ingesting data into chroma")
        collection = chroma_client.get_or_create_collection(
            name=collections_name_faq,
            embedding_function=ef
        )
        df = pd.read_csv(path)
        docs = df['Question'].to_list()
        meta_data = [{'answer': ans} for ans in df['Answer'].to_list()]
        ids = [f'id_{i}' for i in range(len(docs))]

        collection.add(
            documents=docs,
            metadatas=meta_data,
            ids=ids
        )
        print(f'FAQ data successfully ingested to chroma collection: {collections_name_faq}')
    else:
        print(f'Collection {collections_name_faq} is already exist')


def get_relavent_qa(query):
    collection = chroma_client.get_collection(name=collections_name_faq)
    result = collection.query(
        query_texts=[query],
        n_results=2
    )
    return result


def faq_chain(query):
    result = get_relavent_qa(query)
    context = ' '.join([r.get('answer') for r in result['metadatas'][0]])
    answer = generate_answer(query, context)
    return answer


def generate_answer(query, context):
    prompt = f'''
        You are a helpful customer support assistant for Flipkart.
    
    Here is the most relevant frequently asked question: "{query}"
    p
    Here is the existing answer to that question: "{context}"
    
    Based on this information, generate a polite and helpful response to the customer. 
    If additional clarification is needed or if the existing answer doesn't fully cover the user's question,
     extend the answer or ask for more details.
    
    Respond in a clear, professional, and concise manner
    '''
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=os.environ['GROQ_MODEL'],
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    ingest_faq_data(faqs_path)
    query = 'what are the payment method accepted'
    answer = faq_chain(query)
    print("llm answer:\n", answer)
