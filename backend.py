import inspect

# Patch for Python 3.12 (Railway default) - fixes getargspec error
if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec
import os
import re
import json
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import PyPDF2
import docx
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from phi.agent import Agent
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.serpapi_tools import SerpApiTools
from phi.tools.website import WebsiteTools
from phi.model.google import Gemini


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

genai.configure(api_key=GOOGLE_API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class FileRecord(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String)
    pinecone_index = Column(String)
    file_content = Column(Text)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_id = Column(Integer, ForeignKey("files.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

class UserCreate(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    access_token: str
    token_type: str


class FileUploadResponse(BaseModel):
    message: str


class FileInfo(BaseModel):
    id: int
    file_name: str
    file_content: str | None = None

class ChatQuery(BaseModel):
    file_id: int
    query: str
    history: str = ""  


class ChatResponse(BaseModel):
    response: str


class ConversationRecord(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime


def create_pc(api_key: str):
    return Pinecone(api_key=api_key)


def sanitize_file_name(file_name: str) -> str:
    sanitized_name = re.sub('[^a-z0-9-]', '', file_name.strip().lower().replace(" ", "-"))
    return f"faq-{sanitized_name}"


async def parse_file_content(uploaded_file: UploadFile, file_ext: str) -> tuple[str, list[str]]:
    faq_texts = []
    file_content = ""
    if file_ext == ".json":
        file_content = await uploaded_file.file.read().decode("utf-8")
        faq_data = json.loads(file_content)
        faq_texts = [f"Q: {item['question']}\nA: {item['answer']}" for item in faq_data]
    elif file_ext == ".txt":
        file_content = await uploaded_file.file.read().decode("utf-8")
        faq_texts = [chunk.strip() for chunk in file_content.split("\n\n") if chunk.strip()]
    elif file_ext == ".pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file.file)
        file_content = ""
        for page in pdf_reader.pages:
            file_content += page.extract_text() + "\n"
        faq_texts = [chunk.strip() for chunk in file_content.split("\n\n") if chunk.strip()]
    elif file_ext == ".docx":
        doc = docx.Document(uploaded_file.file)
        file_content = "\n".join([para.text for para in doc.paragraphs])
        faq_texts = [chunk.strip() for chunk in file_content.split("\n\n") if chunk.strip()]
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    return file_content, faq_texts


def get_full_faq_text(file_index: str, pc: Pinecone) -> str:
    file_index_instance = pc.Index(file_index)
    res = file_index_instance.query(vector=[0.0] * 768, top_k=1000, include_metadata=True)
    return "\n".join([match["metadata"].get("text", "") for match in res.get("matches", [])])


def modify_query_for_web(query: str, context: str) -> str:
    mod_model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    mod_prompt = f"""
    Given the FAQ Context: {context}
    And the user query: {query}
    Extract only the essential part of the query necessary for a web search.
    Provide a concise modified query focusing on key terms.
    """
    mod_response = mod_model.generate_content(mod_prompt).text
    return mod_response.strip()


def get_web_answer(query: str) -> str:
    prompt = f"Search the web and answer the following question: {query}"
    serp_agent = Agent(
        model=Gemini(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY),
        tools=[DuckDuckGo(), SerpApiTools(api_key=SERPAPI_API_KEY), WebsiteTools()],
        instructions=["Search the web for the most relevant and accurate information to answer the question briefly. Do not ask follow-up questions."]
    )
    try:
        response = serp_agent.run(prompt)
        return response.get_content_as_string()
    except Exception:
        return ""


def gen_summary(text: str) -> str:
    mo = genai.GenerativeModel(model_name="gemini-2.0-flash", 
                                 system_instruction="You are a detailed report generator from the FAQ context. Generate a very detailed analysis report on every detail of the given FAQ context.")
    resp = mo.generate_content(f"Provide a very detailed analysis report regarding everything about the details and information covered based on the given FAQ document context\nFAQ Context: {text}").text
    return resp


def is_unsatisfactory(web_answer: str) -> bool:
    check_model = genai.GenerativeModel(model_name="gemini-2.0-flash", 
        system_instruction="""You are a sentence classifier. Your task is to analyze each provided sentence and determine whether it is "satisfactory" or "not satisfactory" based on the following criteria:
Satisfactory: The sentence conveys a positive meaning, includes clear and sufficient information, and directly provides the answer or solution.
Not Satisfactory: The sentence either lacks enough information, explicitly states that it does not have the answer (e.g., "I don't have the answer"), or fails to address the query effectively."""
    )
    few_shot_prompt = f"""
For each sentence, provide your classification along with a brief explanation of your reasoning.

Example 1:
Input Sentence: "The capital of France is Paris."
Output: Satisfactory – because the sentence gives a clear and correct answer along with necessary information.

Example 2:
Input Sentence: "I don't have the answer."
Output: Not Satisfactory – because it explicitly states a lack of an answer and provides no additional information.

Example 3:
Input Sentence: "I was unable to find the information regarding the data you requested."
Output: Not Satisfactory – because it explicitly states a lack of an answer and provides no additional information.

Example 4:
Input Sentence: "The provided FAQ document does not contain information about who founded ShopTalk. Since I was unable to find the answer using web search, I cannot answer who is the founder of shoptalk."
Output: Not Satisfactory – because it explicitly states a lack of an answer and provides no additional information.

Now, please classify the following sentences:
Sentences: "{web_answer}"
"""
    result = check_model.generate_content(few_shot_prompt).text.lower().strip()
    return "unsatisfactory" in result


def handle_query(query, history, faq_context, vector_store):
    summary = gen_summary(faq_context)  

    classification_prompt = f"""
    You are an FAQ chatbot. Analyze the provided FAQ context and the user query.
- If the query is more like the greeting, closing, or any other general conversation like 'Hello..', 'Greetings..', etc.., respond with "Greeting".
- If the query is not related to the topic of the FAQ context and also the history of the conversation, at all (i.e., less than 10% related), respond with "unrelated".
- If the query is related to the FAQ context and also the history of the conversation, but the answer is not available in the FAQ context, then label it as "needs web search". If after attempting web search the answer is still not found, label it as "keep in db".        
- If the query is answerable directly from the FAQ context, provide the answer using the context.
- If it's a follow-up question (e.g., "Tell me more", "Can you explain further", etc.), label it as "follow up".
    FAQ Context: {faq_context}
    User Query: {query}
    History : {history}
    """
    model = genai.GenerativeModel(model_name='gemini-2.0-flash')
    classification_response = model.generate_content(classification_prompt).text.lower()
    
    if "unrelated" in classification_response:
        alt_response = model.generate_content(f"""
Prompt:
You are a query classifier. Your task is to determine whether a given query is related to the provided reference content. The reference content can be any document—this may include FAQs, articles, bullet points, or any other format—and it can cover any topic.

Instructions:

Reference Content:
You will receive a piece of content. It could be in any format (plain text, JSON, bullet points, etc.) and about any topic or information.

Classification Task:
When you receive a query, use the following rules to classify it:

YES: If the query is related to the content provided.
Example: If the reference is about a workplace collaboration tool and the query asks, "Who is the founder of [tool]?" or "What is meant by the [particular feature] of the [tool] ?" it should be classified as YES, even if the founder's name isn’t mentioned.
NO: If the query is unrelated to the provided content.
Example: If the reference is about a workplace tool and the query asks, "What are Elon Musk's latest projects?" it should be classified as NO.
Output Format:
For each query, respond with either YES or NO (without any additional commentary).

Example Scenario:

Reference Content (any format):
"This document describes a new collaboration tool that helps teams manage projects, share files, and communicate effectively."

Query: "How can teams share files using this tool?"
Output: YES

Query : "What are similar products available in the market?"
Output: YES
                                              
Query: "What is the history of space exploration?"
Output: NO

Now, using these guidelines, classify the following query:
                                                       
{faq_context}
Query: {query}
Output (YES or NO):
""").text
        if "yes" in alt_response.lower():
            vector_store.add_texts([query], namespace="New Queries")
            return "This answer will be provided in the future."
        else:
            return "It is not related to the document."

    elif "greeting" in classification_response:
        greeting_prompt = f"""
        Answer the general user query based on the conversation history, provided
        If the conversation history is empty, provide a general response.
        User Query: {query}
        Chat History: {history}
        """
        return model.generate_content(greeting_prompt).text
        
    elif "needs web search" in classification_response:
        modified_query = modify_query_for_web(query, summary)
        web_answer = get_web_answer(modified_query)
        combined_prompt = f"""
        Answer the following user query using both the FAQ context and the web information.
        If the web information is not relevant or is unable to provide an answer, then perform your own web search and use your own knowledge to answer the User Query based on the provided FAQ Context.
        Consider the Chat history for conversation context.
        User Query: {query}
        FAQ Context: {summary}
        Web Information: {web_answer}
        Chat History: {history}

        Note : In the response, do not provide like, "As per the FAQ context, the answer is" or "Based on the provided FAQ Context". Instead, provide the answer directly.
        Note: In the response, do not provide anything like 'I found this information on the web' or 'I searched the web for you' or 'Based on the provided FAQ Context'. Instead, provide the answer directly.
        Note : The answer should always be on support of the FAQ context.
        """
        final_response = model.generate_content(combined_prompt).text
        if not final_response.strip() or is_unsatisfactory(final_response):
            vector_store.add_texts([query], namespace="New Queries")
            return "This answer will be provided in the future."
        else:
            vector_store.add_texts([f"Query: {query}\nResponse: {final_response}"], namespace="Web Queries")
            return final_response
    elif "follow up" in classification_response:
        follow_up_prompt = f"""
        Answer the user query based on the provided FAQ context and the chat history.
        User Query: {query}
        FAQ Context Summary: {summary}
        Chat History: {history}
        """
        return model.generate_content(follow_up_prompt).text
    else:
        prompt = f"User Query: {query}\nFAQ Context Summary: {summary}\nChat History: {history}\nProvide a direct answer."
        return model.generate_content(prompt).text


def store_conversation(db: Session, user_id: int, file_id: int, role: str, content: str):
    conv = Conversation(user_id=user_id, file_id=file_id, role=role, content=content)
    db.add(conv)
    db.commit()
    db.refresh(conv)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Signup successful. Please log in."}


@app.post("/login", response_model=TokenData)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username, User.password == form_data.password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    pinecone_api_key: str = Form(...),
    file_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pc = create_pc(pinecone_api_key)
    file_ext = os.path.splitext(file.filename)[1].lower()
    try:
        file_content, faq_texts = await parse_file_content(file, file_ext)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    file_index = sanitize_file_name(file_name)
    
    indexes = [i['name'] for i in pc.list_indexes()]
    if file_index not in indexes:
        pc.create_index(
            name=file_index,
            dimension=768,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1'),
        )
    file_index_instance = pc.Index(file_index)
    file_vector_store = PineconeVectorStore(index=file_index_instance, embedding=embeddings)
    file_vector_store.add_texts(faq_texts)
    
    new_file = FileRecord(user_id=current_user.id, file_name=file_name, pinecone_index=file_index, file_content=file_content)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return {"message": "File uploaded and processed successfully!"}


@app.get("/files", response_model=list[FileInfo])
def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(FileRecord).filter(FileRecord.user_id == current_user.id).all()
    return [{"id": f.id, "file_name": f.file_name} for f in files]


@app.get("/files/{file_id}", response_model=FileInfo)
def get_file(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.user_id == current_user.id).first()
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")
    return {"id": file_rec.id, "file_name": file_rec.file_name, "file_content": file_rec.file_content}

@app.post("/chat/query", response_model=ChatResponse)
def chat_query(
    pinecone_api_key: str = Form(...),
    file_id: int = Form(...),
    query: str = Form(...),
    history: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    file_rec = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.user_id == current_user.id).first()
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")
    
    pc = create_pc(pinecone_api_key)
    vector_store = PineconeVectorStore(index=pc.Index(file_rec.pinecone_index), embedding=embeddings)
    faq_context = get_full_faq_text(file_rec.pinecone_index, pc)
        
    history_str = history  
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    user_query = model.generate_content(
                    f"""
                    Rewrite the given query to remove pronouns and clarify shortcuts.
                    Consider the following common shortcuts: "shld = should", "wt = what", "abt = about", "wdym = what do you mean", "exp = explain", "plz = please", "u = you", "r = are", "w = with", "w/o = without", "wrt = with respect to", "wrt = with regard to", "wrt = with reference to".
                    Example 1:
                    Input: What is shoptalk
                    Output: Who are shoptalk competitors?
                    Example 2:
                    Input: Explain the features of shoptalk
                    Output: Explain the features of shoptalk in detail
                    Example 3:
                    Input: What is the pricing of shoptalk
                    Output: Explain about the pricing of shoptalk in detail

                    User Query: {query}
                    Chat History: {history}
                    Output: Provide only the modified query as a single sentence."""
                ).text.strip()   
    
    bot_response = handle_query(user_query, history_str, faq_context, vector_store)
    store_conversation(db, current_user.id, file_rec.id, "user", query)
    store_conversation(db, current_user.id, file_rec.id, "assistant", bot_response)
    
    return {"response": bot_response}



@app.get("/chat/history/{file_id}", response_model=list[ConversationRecord])
def chat_history(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convs = db.query(Conversation).filter(Conversation.file_id == file_id, Conversation.user_id == current_user.id).order_by(Conversation.timestamp).all()
    return [
        ConversationRecord(
            id=c.id,
            role=c.role,
            content=c.content,
            timestamp=c.timestamp
        )
        for c in convs
    ]

@app.post("/config/pinecone")
def config_pinecone(pinecone_api_key: str = Form(...)):
    try:
        pc = create_pc(pinecone_api_key)
        return {"message": "Pinecone API key is valid."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

