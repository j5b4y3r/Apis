import os
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from bs4 import BeautifulSoup as bs

app = FastAPI(title="Storyblocks Helper API")

# --- Models ---

class VideoResult(BaseModel):
    title: str
    link: str

class DownloadLinkResponse(BaseModel):
    original_link: str
    download_url: str

# --- Logic ---

def search_storyblocks_video(query: str, num_videos: int = 5):
    query_parts = query.split()
    if not query_parts:
        return []
    
    first_word = query_parts[0].lower()
    video_info = []
    
    search_urls = [
        f"https://www.storyblocks.com/all-video/search/{query.replace(' ', '%20')}",
        f"https://www.storyblocks.com/all-video/search/{first_word}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for url in search_urls:
        if len(video_info) >= num_videos:
            break
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: continue
            
            soup = bs(response.content, "html.parser")
            video_cards = soup.find_all("div", {"data-testid": "video-stock-item-card"})
            
            for card in video_cards:
                if len(video_info) >= num_videos: break
                title_el = card.find("h3")
                if title_el and first_word in title_el.text.lower():
                    link_el = card.find("a")
                    if link_el:
                        video_info.append({
                            "title": title_el.text.strip(),
                            "link": "https://www.storyblocks.com" + link_el.get("href")
                        })
        except:
            continue
    return video_info

def extract_download_url(storyblocks_url: str):
    base_url = "https://steptodown.com/storyblocks-downloader/get.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://steptodown.com/storyblocks-downloader/",
        "Origin": "https://steptodown.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "cf_clearance=cR08Dn6lrvAYwrzrYtx9p1wTyJqL1fN4eTuRjytkbWM-1773742105-1.2.1.1-MItCwzZakxm1IMfcLQvIwbNNQGoUIVqIkwlRurLHZ4S5nF9DWejpngy5w182n1t_pFij2Y88CHH5vh5Xs79n3bUNAZZ7XxhTKMjmlC863dHVlw8kClyJ_uwC_TYq1jSK9exQSr_hiBUB5xNqIiI9KI6YMAnDxpVfgGpjhfROgsqpiCmsXGwMkhcFOu.U6Cf_M6W_vrHvXt94tmn3UVqIOHadUKw9ZMXa90EMJjLxKtE; pll_language=en; PHPSESSID=u9rnmh6b90dadl7qgqk18rl9p4",
        "Host": "steptodown.com",
        "Sec-Fetch-Site": "same-origin",
    }
    try:
        rs = requests.post(base_url, data={"url": storyblocks_url}, headers=headers, timeout=15)
        soup = bs(rs.content, "html.parser")
        btn = soup.find("li", {"class": "watch"}).find("a", {"class": "btn"})
        return f"https://steptodown.com/storyblocks-downloader/{btn.get('href')}"
    except:
        return None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "Storyblocks API is running on Render."}

@app.get("/search", response_model=List[VideoResult])
async def search(q: str, limit: int = 5):
    return search_storyblocks_video(q, limit)

@app.get("/get-download-link", response_model=DownloadLinkResponse)
async def get_link(url: str):
    dl_url = extract_download_url(url)
    if not dl_url:
        raise HTTPException(status_code=502, detail="Failed to extract link")
    return {"original_link": url, "download_url": dl_url}

if __name__ == "__main__":
    import uvicorn
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
