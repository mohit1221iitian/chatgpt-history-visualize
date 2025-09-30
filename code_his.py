import json
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

load_dotenv()

embedding_llm=HuggingFaceEmbeddings(
    # model_name="BAAI/bge-large-en-v1.5"
    model_name="sentence-transformers/all-MiniLM-L6-v2" 
)

with open("conversations.json", "r", encoding="utf-8") as f:
    data = json.load(f)
# print(data[1])
conversations = []
for convo in data:
    mapping = convo.get("mapping", {})
    prev_user_msg = None  
    for node_id, node_data in mapping.items():
        msg = node_data.get("message")
        if not msg:
            continue
        role = msg.get("author", {}).get("role")
        parts = msg.get("content", {}).get("parts", [])
        text = " ".join(str(p) for p in parts if isinstance(p, (str, int, float))).strip()
        if not text:
            continue
        if role == "user":
            prev_user_msg = text
        elif role == "assistant" and prev_user_msg:
            conversations.append(f"User: {prev_user_msg}\nAssistant: {text}")
            prev_user_msg = None
# print(conversations[0])

embedding_vector=embedding_llm.embed_documents(conversations)

similarity_matrix=cosine_similarity(embedding_vector)
threshold=0.6

edges=[]
for i in range(len(similarity_matrix)):
    for j in range(i+1,len(similarity_matrix)):
        if similarity_matrix[i][j]>threshold:
            edges.append((i,j,similarity_matrix[i][j]))

G=nx.Graph()

for i,text in enumerate(conversations):
    G.add_node(i,label=f"chat {i}",text=text)
for src,des,weight in edges:
    G.add_edge(src,des,weight=weight)

net = Network(height="1000px", width="100%", bgcolor="#0d0d0d", font_color="white", notebook=False)
net.from_nx(G)
net.show_buttons(filter_=['physics'])

try:
    net.show("chat_history_graph.html")
except AttributeError:
    net.write_html("chat_history_graph.html", notebook=False)