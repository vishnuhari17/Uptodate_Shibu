
# UpToDate-Shibu 📸📰

**UpToDate-Shibu** is an AI-powered Instagram automation bot that fetches trending tech news, transforms them into engaging carousel posts, and publishes them — completely hands-free. Now with support for **scheduled posting** and **Docker deployment**.

> ⚡️ Your intelligent, 24/7 Instagram content generator.

---

## 🚀 Features

- 🔍 **Auto-News Curation**: Gathers trending and viral-worthy articles using the [News API](https://newsapi.org/).
- 🤖 **AI-Driven Content Generation**: Uses **Gemini (Google Generative AI)** to create Instagram carousel slides with strong storytelling.
- 🖼️ **Visual Image Matching**: Automatically selects contextually relevant, unique images from **Unsplash API**.
- 📝 **Dynamic Text Overlays**: Applies well-styled, readable text over selected images using **Pillow** and custom fonts.
- ☁️ **Cloud Upload**: Uploads content to **Cloudinary**.
- 📲 **Instagram Publishing**: Posts directly to Instagram via **Meta Graph API**.
- 🕓 **Automated Scheduling**: Posts every 77 minutes (5 times/day) using a lightweight scheduler.
- 🐳 **Dockerized**: Runs seamlessly in a Docker container for cloud or local deployment.

---

## 📂 Project Structure

```

UpToDate-Shibu/
├── fonts/
│   ├── Montserrat-Bold.ttf
│   └── Montserrat-Regular.ttf
├── input\_images/
├── output\_images/
├── uptodate\_shibu.py
├── scheduler\_runner.py
├── carousel.json
├── published\_articles.json
├── requirements.txt
├── .env
└── Dockerfile

````

---

## 🛠️ Requirements

Install Python dependencies locally using:

```bash
pip install -r requirements.txt
````

Or use Docker (see below).

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following:

```env
NEWS_API_KEY=your_newsapi_key
IMAGE_API_KEY=your_unsplash_key
GEMINI_API_KEY=your_google_gemini_key
INSTAGRAM_ACCESS_TOKEN=your_meta_graph_token
IG_USER_ID=your_instagram_business_user_id
```

---

## 🧪 Usage

### ▶️ Run Once Locally

```bash
python uptodate_shibu.py
```

### 🔁 Run Automatically Every 77 Minutes

`scheduler_runner.py` handles scheduled posting:

```python
# scheduler_runner.py
import schedule
import time
from uptodate_shibu import main

def job():
    print("Running AI Post Bot...")
    main()

# Schedule 5 posts per day (every 77 minutes)
schedule.every(77).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Run it with:

```bash
python scheduler_runner.py
```

---

## 🐳 Docker Support

Build and run in a containerized environment:

### 🛠️ Dockerfile

```dockerfile
FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "scheduler_runner.py"]
```

### 🔧 Build and Run

```bash
docker build -t uptodate-shibu .
docker run --env-file .env uptodate-shibu
```

> You can deploy this container to a VPS or cloud provider for continuous operation.

---

## 📌 Privacy Notice

No personal or user data is shared with any 3rd-party services. Only news article metadata is sent to Gemini and API services.

---

## 📷 Optional: Screenshots

![sample post](https://raw.githubusercontent.com/vishnuhari17/Uptodate_Shibu/sample.png?raw=true)
---

## 📄 License

MIT License

---

## 👨‍💻 Author

Created by [Vishnuhari V A](https://github.com/vishnuhari17)

