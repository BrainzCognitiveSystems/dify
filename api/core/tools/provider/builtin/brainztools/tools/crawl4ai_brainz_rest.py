

import requests
import json
import base64

url = "https://www.nbcnews.com/business"
url = "https://dify.ai/"

data = {
  "urls": [url],
  "include_raw_html": True,
  "word_count_threshold": 10,
  "extraction_strategy": "NoExtractionStrategy",
  "chunking_strategy": "RegexChunking",
  "screenshot": True
}
crawl4ai_endpoint = "https://crawl4ai.com/crawl"
crawl4ai_endpoint = "http://localhost:8098/crawl"

# See: GUI Old Interface : http://localhost:8098/old

response = requests.post(crawl4ai_endpoint, json=data)
try:
    answer = response.content.decode('utf-8')
    json_response = json.loads(answer)
    result = json_response['results'][0]
    txt = json.dumps(result, indent=4)
    try:
        # from : JPG img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        img_base64 = result['screenshot']
        base64_img_bytes = img_base64.encode('utf-8')
        decoded_image_data = base64.decodebytes(base64_img_bytes)
        with open('screenshot.jpg', 'wb') as file_to_save:
            file_to_save.write(decoded_image_data)
    except:
        pass
    print(txt)
except:
    print(response.json())


"""
curl -X POST -H "Content-Type: application/json" -d '{
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "include_raw_html": true,
  "word_count_threshold": 10,
  "extraction_strategy": "NoExtractionStrategy",
  "chunking_strategy": "RegexChunking",
  "screenshot": true
}' https://crawl4ai.com/crawl
"""

