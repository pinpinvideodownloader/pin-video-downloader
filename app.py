from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Função para extrair o link do vídeo do Pinterest
def get_pinterest_video(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Fazendo requisição para o link
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return None
        
        # Analisando o HTML da página
        soup = BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")
        
        for script in scripts:
            if "video_list" in script.text:
                match = re.search(r'"url":"(https:[^"]+)"', script.text)
                if match:
                    video_url = match.group(1).replace("\u0026", "&")
                    return video_url
        
        return None
    except Exception as e:
        return None

# Rota para processar o download do vídeo
@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    pinterest_url = data.get("url")

    if not pinterest_url:
        return jsonify({"error": "URL do Pinterest é obrigatória"}), 400

    video_url = get_pinterest_video(pinterest_url)

    if video_url:
        return jsonify({"video_url": video_url})
    else:
        return jsonify({"error": "Não foi possível obter o vídeo"}), 400

# Iniciar o servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
