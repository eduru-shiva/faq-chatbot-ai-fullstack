# FAQ Chatbot AI - Full Stack App

FAQ Chatbot AI is a full-stack application that allows users to upload FAQ documents (in PDF, DOCX, TXT, or JSON format) and interact with them via a chat interface. The backend is built with FastAPI and uses advanced generative AI models along with vector search via Pinecone to answer user queries based on the uploaded FAQ content. The frontend is built with React and React-Bootstrap, providing user authentication, file management, and an interactive chat experience.

## Features

- **User Authentication:** Secure signup and login using JWT.
- **File Upload & Processing:** Upload files (PDF, DOCX, TXT, JSON) to extract FAQ content and index it using Pinecone.
- **Chat Interface:** Ask questions related to the uploaded FAQ document and receive answers generated with Google Generative AI.
- **Conversation History:** Keep track of past interactions per file.
- **Web Query Integration:** If the answer isn’t found directly in the FAQ content, the application performs a web search and integrates that data.
- **Environment Configuration:** Easily switch API keys and settings using environment variables.

## Project Structure (Only Required Files Included)

```
faq-chatbot-ai-fullstack/
├── backend.py              # FastAPI backend code
├── app.db                  # SQLite database (generated after first run)
├── .env                    # Environment variables (see below)
├── requirements.txt        # Python dependencies for the backend
└── react-app/           # React frontend application
    ├── public/
    └── src/
        ├── components/     # React components (Auth, Chat, FileList, Main, Sidebar)
        ├── contexts/       # React Context for Authentication
        ├── App.jsx         # Main React app entry point
        └── main.jsx        # React DOM entry point
```

## Prerequisites

### Backend

- Python 3.9 or higher
- [Pinecone](https://www.pinecone.io/) account and API key
- [Google Generative AI](https://developers.generativeai.google/) API key
- [SerpAPI](https://serpapi.com/) API key

### Frontend

- Node.js (version 14 or higher)
- npm or yarn package manager

## Setup & Installation

### 1. Backend Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Jnan-py/faq-chatbot-ai-fullstack.git
   cd faq-chatbot-ai-fullstack
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**

   Create a `.env` file in the project root and set the following variables:

   ```env
   GOOGLE_API_KEY=your_google_api_key
   SERPAPI_API_KEY=your_serpapi_api_key
   SECRET_KEY=your_secret_key
   ```

5. **Run the Backend Server:**

   ```bash
   uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
   ```

   The backend server should now be running at `http://localhost:8000`.

### 2. Frontend Setup

1. **Navigate to the React app folder:**

   ```bash
   cd react-app
   ```

2. **Install npm dependencies:**

   ```bash
   npm install
   ```

3. **Run the Frontend:**

   ```bash
   npm run dev
   ```

   The frontend should now be running, and you can access it in your browser at `http://localhost:5173`.

## Usage

1. **Signup & Login:**

   - Access the login page to sign up or log in.
   - Once logged in, you will be redirected to the main interface.

2. **Upload FAQ File:**

   - In the sidebar, enter your Pinecone API key and upload your FAQ file (enter a file name and select the file).
   - The file will be processed and indexed for FAQ retrieval.

3. **Chat with the FAQ Bot:**
   - Select an uploaded file from the sidebar.
   - Switch to the Chat tab and type your query. The application will use the FAQ content (and web search if needed) to answer your query.
   - Your conversation history is maintained per file.

## Technologies Used

- **Backend:** FastAPI, SQLAlchemy, SQLite, JWT, Pinecone, Google Generative AI, LangChain tools.
- **Frontend:** React, React-Bootstrap, React Router, Axios.

## Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

_Note:_

- Ensure that the package names (e.g., `google-generativeai`, `pinecone-client`, `phidata`) match the ones available on PyPI or your internal package names.
- If you encounter issues with any of the packages, check the documentation or use appropriate version specifiers.
