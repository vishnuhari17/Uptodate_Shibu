import os
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import json

from dotenv import load_dotenv

from PIL import Image, ImageDraw, ImageFont

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
UNSPLASH_API_KEY = os.getenv("IMAGE_API_KEY")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_news():
    """
    Get news articles from the News API.
    """
    import requests
    from datetime import datetime, timedelta


    # Define the API endpoint and parameters
    url = "https://newsapi.org/v2/everything"
    query = "technology"
    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "sortBy": "popularity",
        "apiKey": NEWS_API_KEY,
    }

    # Make the request to the News API
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return articles
    else:
        print(f"Error: {response.status_code}")
        return []
    
def select_interesting_articles(articles):

    class BestArticle(BaseModel):
        title: str
        url: str
        description: str
        image_url: str
        content: str
        published_at: str
        source: str
        why_interesting: str
    response = client.models.generate_content(
        model="gemini-2.0-flash",
       contents=(
            "You're a social media trend expert. From the following list of articles, select the ones that are most likely to go viral or instantly grab attention on an Instagram tech news page. "
            "Only choose articles that are visually appealing, have a strong headline hook, and cover trending or emotionally engaging topics. "
            "Output only the title and URL of the selected articles.\n\n"
            f"{str(articles)}"
        ),

        config={
            'response_mime_type': 'application/json',
            'response_schema' : list[BestArticle],
        }
    )

    selected_articles : list[BestArticle] = response.parsed

    return selected_articles

def review_articles(articles):
    class Article(BaseModel):
        title: str
        url: str
        image_url: str

    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            "You are a content strategist for a tech Instagram page. Review the following articles and select the one that has the highest potential to go viral on Instagram. "
            "The ideal post is engaging, informative, and explains a current trending topic in a way that can be split into multiple bite-sized carousel slides. "
            "The story must have visual storytelling potential, emotional relatability, and share-worthiness.\n\n"
            f"{str(articles)}"
        ),

        config={
            'response_mime_type': 'application/json',
            'response_schema' : Article,
        }
    )

    selected_article : Article = response.parsed
    return selected_article

def scrape_article(article):
    """
    Scrape the article for content.
    """
    url = article.url
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text() for para in paragraphs])
        return content
    else:
        print(f"Error: {response.status_code}")
        return ""

def post_content_generation(content):
    """
    Generate content for the post.
    """

    class CarouselSlide(BaseModel):
        heading: str
        text: str
        image_search_keyword: str

    class Carousel(BaseModel):
        slides: list[CarouselSlide]
        detailed_caption: str

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            "You are an expert social media storyteller. Create a 5-slide minimum Instagram carousel post from the following article content.\n\n"
            "Each slide should have:\n"
            "- A clear heading or point (like a tweet-sized fact or insight)\n"
            "- Short, engaging copy (max 3 lines)\n"
            "- A relevant image search keyword (avoid vague terms)\n\n"
            "The flow should follow a story arc: hook → context → development → takeaway → final thought or call to action.\n\n"
            "Make sure the post can be understood without reading the original article. It should provide complete value in carousel form.\n\n"
            "After the carousel content, write a long-form caption summarizing the full news story with good storytelling and relevant hashtags.\n"
            "Do not include hashtags in the slides, only in the caption.\n\n"
            f"Article Content:\n{content}"
        ),

        config={
            'response_mime_type': 'application/json',
            'response_schema' : Carousel,
        }
    )

    generated_content = response.parsed
    return generated_content



def get_image(image_search_keyword):
    """
    Get a list of images from Unsplash based on the search keyword.
    """
    images = []
    image_search_keyword = "-".join(image_search_keyword.split())

    url = f"https://api.unsplash.com/search/photos?page=1&query={image_search_keyword}&client_id={UNSPLASH_API_KEY}&orientation=squarish"
    response = requests.get(url)


    if response.status_code == 200:
        results = response.json().get("results", [])
        for result in results:
            image_url = result.get("urls", {}).get("regular", "")
            image_alt_text = result.get("alt_description", "")
            if image_url:
                images.append({
                    "image_url": image_url,
                    "alt_text": image_alt_text or "",
                })
        return images
    else:
        print(f"Error fetching images: {response.status_code}")
        print(f"Response: {response.text}")
        return []

def select_image(images, image_search_keyword, exclude_urls=None):
    """
    Use LLM to select the best image from the list of images,
    excluding any URLs passed in `exclude_urls`.
    """
    if not images:
        print("No images available to select from.")
        return None

    if exclude_urls:
        images = [img for img in images if img["image_url"] not in exclude_urls]

    if not images:
        print("All images are excluded. Cannot select a new one.")
        return None

    class SelectedImage(BaseModel):
        image_url: str

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"You are a visual content curator. Select the best image from the list below to match this Instagram slide topic: '{image_search_keyword}'.\n"
            f"The image should directly support the meaning or emotion of the content.\n"
            f"Here are the options:\n{images}"
        ),
        
        config={
            'response_mime_type': 'application/json',
            'response_schema': SelectedImage,
        },
    )

    selected_image = response.parsed
    return selected_image.image_url


def generate_carousel_images(carousel):
    """
    Generate a list of image entries for the carousel, ensuring all selected images are unique.
    """
    final_images = []
    used_urls = set()

    for item in carousel.slides:
        possible_images = get_image(item.image_search_keyword)
        if not possible_images:
            continue

        final_image_url = select_image(possible_images, item.image_search_keyword, exclude_urls=used_urls)

        if not final_image_url:
            continue  # Skip if no valid image found

        # Add selected image to used URLs
        used_urls.add(final_image_url)

        final_images.append({
            "heading": item.heading,
            "text": item.text,
            "image_url": final_image_url,
            "image_search_keyword": item.image_search_keyword,
        })

    return final_images



def download_image(image_url, image_search_keyword):
    """
    Download the image from the given URL and save it to the input_images folder.
    """
    os.makedirs("input_images", exist_ok=True)

    filename = image_search_keyword.replace(" ", "_") + ".jpg"
    filepath = os.path.join("input_images", filename)

    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Image downloaded to {filepath}")
            return filepath
        else:
            print(f"Error downloading image: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception while downloading image: {e}")
        return None



def overlay_text_on_image(image_path, heading, text, output_filename=None):
    try:
        os.makedirs("output_images", exist_ok=True)

        # Load image
        image = Image.open(image_path).convert("RGBA")
        width, height = image.size

        # Create overlay
        txt_overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_overlay)

        font_path_bold = "fonts/Montserrat-Bold.ttf"
        font_path_regular = "fonts/Montserrat-Regular.ttf"

        max_font_size = int(height * 0.045)
        min_font_size = 12

        max_text_width = width - 60
        max_text_height_ratio = 0.40  # Max 40% for both heading+text

        # Text wrapper function
        def wrap_text(font_path, font_size, text):
            font = ImageFont.truetype(font_path, font_size)
            lines, heights = [], []
            line = ""
            for word in text.split():
                test_line = f"{line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] <= max_text_width:
                    line = test_line
                else:
                    lines.append(line)
                    heights.append(bbox[3] - bbox[1])
                    line = word
            if line:
                lines.append(line)
                bbox = draw.textbbox((0, 0), line, font=font)
                heights.append(bbox[3] - bbox[1])
            total_height = sum(heights) + (len(lines) - 1) * 10
            return lines, heights, total_height, font

        # Fit heading
        heading_font_size = max_font_size
        while heading_font_size >= min_font_size:
            heading_lines, heading_heights, heading_total_height, heading_font = wrap_text(
                font_path_bold, heading_font_size, heading
            )
            if heading_total_height <= height * 0.15:
                break
            heading_font_size -= 1

        # Fit body text
        body_font_size = max_font_size - 4
        while body_font_size >= min_font_size:
            body_lines, body_heights, body_total_height, body_font = wrap_text(
                font_path_regular, body_font_size, text
            )
            combined_height = heading_total_height + body_total_height + 40
            if combined_height <= height * max_text_height_ratio:
                break
            body_font_size -= 1

        total_overlay_height = heading_total_height + body_total_height + 40
        y = height - total_overlay_height - 30

        def draw_text_block(lines, heights, font, y_start, padding=10, radius=8, fill=(0, 0, 0, 160), color=(255, 255, 255, 255)):
            y = y_start
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = heights[i]
                x = (width - text_width) // 2

                # Draw rounded rectangle
                box = [x - padding, y - 5, x + text_width + padding, y + text_height + 15]
                draw.rounded_rectangle(box, radius=radius, fill=fill)

                # Draw text
                draw.text((x, y), line, font=font, fill=color)
                y += text_height + 15
            return y

        # Draw heading first (visually bold)
        y = draw_text_block(
            heading_lines,
            heading_heights,
            heading_font,
            y_start=y,
            fill=(0, 0, 0, 220),
            color=(255, 255, 255, 255)
        )

        y += 20

        # Draw body below it
        draw_text_block(
            body_lines,
            body_heights,
            body_font,
            y_start=y,
            fill=(0, 0, 0, 160),
            color=(255, 255, 255, 255)
        )

        # Combine and save
        final_image = Image.alpha_composite(image, txt_overlay).convert("RGB")
        if not output_filename:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_filename = base_name + "_overlay.jpg"

        output_path = os.path.join("output_images", output_filename)
        final_image.save(output_path, "JPEG")
        

    except Exception as e:
        print(f"Error overlaying text on image: {e}")


import cloudinary
import cloudinary.uploader

# Config
cloudinary.config(secure=True)



def upload_to_cloudinary(image_path):
    image_path = os.path.join("output_images", image_path)
    result = cloudinary.uploader.upload(image_path, resource_type="image")
    return result.get("secure_url")


def convert_to_post(carousel, caption):
    uploaded_urls = []
    for item in carousel:
        # Download the image from the image URL
        filename = download_image(item["image_url"], item["image_search_keyword"])
        if filename:
            # Overlay text on the downloaded image
            output_path = f"output_{item['image_search_keyword'].replace(' ', '_')}.jpg"
            overlay_text_on_image(filename,item["heading"], item["text"], output_path)
            # Upload the image to imgbb
            imgbb_url = upload_to_cloudinary(output_path)
            if imgbb_url:
                print(f"Image uploaded to imgbb: {imgbb_url}")
                uploaded_urls.append(imgbb_url)
            else:
                print("Failed to upload image.")
            
            # Here you can add code to upload the image to Instagram
            print(f"Image saved as {output_path} with description: {item['heading']}")
        else:
            print("Failed to download image.")
    
    post_carousel_to_instagram(caption, uploaded_urls)
        



ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")  # Instagram Business Account ID

def post_carousel_to_instagram(caption, image_urls):
    # Step 1: Upload each image and get container IDs
    container_ids = []

    for image_url in image_urls:
        image_data = {
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": ACCESS_TOKEN
        }
        res = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
            data=image_data
        )
        if res.status_code == 200:
            container_id = res.json()["id"]
            container_ids.append(container_id)
            print(f"Uploaded image container: {container_id}")
        else:
            print(f"Error uploading image to container: {res.text}")

    if not container_ids:
        print("No containers created. Aborting post.")
        return None

    # Step 2: Create a carousel post with those container IDs
    carousel_data = {
        "media_type": "CAROUSEL",
        "children": container_ids,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }

    res = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
        json=carousel_data
    )

    if res.status_code != 200:
        print(f"Error creating carousel: {res.text}")
        return None

    creation_id = res.json()["id"]
    print(f"Carousel container created: {creation_id}")

    # Step 3: Publish the carousel post
    publish_data = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }

    res = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media_publish",
        data=publish_data
    )

    if res.status_code == 200:
        print(f"Successfully published carousel! Post ID: {res.json()['id']}")
    else:
        print(f"Error publishing carousel: {res.text}")


    
def main():
    """
    Main function to run the script.
    """
    articles = get_news()
    selected_articles = select_interesting_articles(articles)
    selected_article = review_articles(selected_articles)
    print(f"Selected article: {selected_article.title}")
    content = scrape_article(selected_article)
    post = post_content_generation(content)
    carousel = generate_carousel_images(post)
    # Save the carousel object as JSON for development purposes
    with open("carousel.json", "w") as json_file:
        json.dump(carousel, json_file, indent=4)  # Removed .dict() since carousel is a list
        print("Carousel saved to carousel.json for development.")
    # Load the carousel data from carousel.json
    # with open("carousel.json", "r") as json_file:
    #     carousel = json.load(json_file)
    convert_to_post(carousel, post.detailed_caption)
    # print(f"Detailed caption: {post.detailed_caption}")


if __name__ == "__main__":
    main()