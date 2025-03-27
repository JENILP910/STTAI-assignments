import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# Backend runs on port 9567
# BACKEND_URL = "http://localhost:8000"
# BACKEND_URL = "http://backend:9567"
BACKEND_URL = "http://http://10.128.0.3:9567:9567"

html = """
<html>
<body>
    <h2>FastAPI Elasticsearch Frontend</h2>
    <input id='textInput' type='text' placeholder='Enter text to insert'>
    <button onclick='insertText()'>Insert</button>
    <br><br>
    <input id='searchQuery' type='text' placeholder='Enter search query'>
    <button onclick='getBest()'>Search</button>
    <div id='output'></div>

    <script>
        function insertText() {
            let text = document.getElementById('textInput').value;
            fetch('/insert', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'text=' + encodeURIComponent(text)
            })
            .then(response => response.json())
            .then(data => {
                if (data.message === "Stored successfully") {
                    document.getElementById('output').innerText = `Stored successfully!\nID: ${data.id}\nText: ${data.text}`;
                } else {
                    document.getElementById('output').innerText = 'Failed to store data';
                }
            })
            .catch(error => {
                document.getElementById('output').innerText = 'Error: ' + error;
            });
        }

        function getBest() {
            let query = document.getElementById('searchQuery').value;
            fetch(`/search?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                let outputDiv = document.getElementById('output');
                if (data.message === "Best document found") {
                    outputDiv.innerText = `Best Document Found:\nID: ${data.id}\nText: ${data.text}`;
                } else {
                    outputDiv.innerText = 'No data found';
                }
            })
            .catch(error => {
                document.getElementById('output').innerText = 'Error: ' + error;
            });
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return html

@app.post("/insert")
def insert(text: str = Form(...)):
    try:
        response = requests.post(f"{BACKEND_URL}/insert", data={"text": text})
        return response.json()
    except Exception as e:
        return {"message": "Backend error", "error": str(e)}

@app.get("/search")
def search(query: str):
    try:
        response = requests.get(f"{BACKEND_URL}/search", params={"query": query})
        return response.json()
    except Exception as e:
        return {"message": "Backend error", "error": str(e)}
