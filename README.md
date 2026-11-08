# Movie Watchlist API — GDGoC UGM Backend Assignment

A RESTful backend API for managing a movie watchlist, user reviews, and AI-powered recommendations built using **FastAPI**, **SQLModel (SQLite)**, **JWT Authentication**, and **Google Gemini API**.

---

## 🛠 Tech Stack

* **Framework:** FastAPI (Python 3.10+)
* **Database & ORM:** SQLite & SQLModel (SQLAlchemy + Pydantic)
* **Authentication:** OAuth2 with Password Hashing (`passlib` + `bcrypt`) & JWT Tokens (`python-jose`)
* **AI Integration:** Google Gemini API (`google-generativeai`)
* **Deployment:** Render

---

## 📋 Prerequisites

Make sure you have the following installed on your machine:
* **Python 3.10+**
* **Git**
* A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory of your project based on the following template:

```env
# Secret key for JWT encoding/decoding
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256

# Database Connection (SQLite local file)
DATABASE_URL=sqlite:///database.db

# Google Gemini AI API Key
GEMINI_API_KEY=your_gemini_api_key_here
