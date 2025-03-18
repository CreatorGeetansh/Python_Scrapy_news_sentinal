from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import uuid  # For generating unique IDs
from groq import Groq
import json
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Initialize Groq client
import os
client = Groq(api_key=os.getenv("GOQ_API_KEY"))


def extract_location_and_crime_type(headline):
    """
    Use Groq API to extract location and crime type from the headline.
    """
    try:
        # Send a request to the Groq API
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Extract the most precise LOCATION inside DELHI NCR and STRICLTY IDENTIFY THE CRIME TYPE from the following headline: '{headline}'.
                    Return the output as a valid JSON object with keys 'location' and 'crime_type'.
                    Example:
                    {{
                        "location": "Connaught Place",
                        "crime_type": "Robbery"
                    }}
                    Ensure the response is a valid JSON object and does not contain any additional text.
                    """
                }
            ],
            model="llama3-8b-8192"
        )

        # Get the response content
        result = response.choices[0].message.content

        # Debug: Print the raw response
        # print(f"Raw Groq API response: {result}")

        # Extract JSON object from the response
        try:
            # Remove any leading/trailing whitespace or invalid characters
            result = result.strip()

            # Find the start and end of the JSON object
            json_start = result.find("{")
            json_end = result.rfind("}") + 1

            # Extract the JSON object
            if json_start != -1 and json_end != -1:
                json_str = result[json_start:json_end]
                extracted_data = json.loads(json_str)
                return extracted_data
            else:
                print("No JSON object found in the response.")
                return {"location": "Delhi", "crime_type": "N/A"}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            # print(f"Raw response: {result}")
            return {"location": "Delhi", "crime_type": "N/A"}
    except Exception as e:
        print(f"Error extracting location and crime type: {e}")
        return {"location": "Delhi", "crime_type": "N/A"}

def scrape_ndtv_news():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues

    # Initialize the WebDriver
    try:
        print("Initializing WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=Options)
        print("WebDriver initialized successfully.")
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return []

    # Load the webpage
    url = "https://www.ndtv.com/delhi-news#pfrom=home-ndtv_mainnavigation"
    try:
        print(f"Loading webpage: {url}")
        driver.get(url)
        print("Webpage loaded successfully.")
    except Exception as e:
        print(f"Error loading webpage: {e}")
        driver.quit()
        return []

    # Wait for the page to load (adjust sleep time as needed)
    print("Waiting for the page to load...")
    time.sleep(5)  # Increase this if the content takes longer to load

    # Simulate scrolling to load all content
    try:
        print("Simulating scrolling to load more content...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new content to load

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Exit the loop if no new content is loaded
            last_height = new_height
        print("Scrolling completed.")
    except Exception as e:
        print(f"Error during scrolling: {e}")

    # Get the page source after all content is loaded
    try:
        print("Extracting page source...")
        page_source = driver.page_source
        print("Page source extracted successfully.")
    except Exception as e:
        print(f"Error extracting page source: {e}")
        driver.quit()
        return []

    # Close the browser
    print("Closing WebDriver...")
    driver.quit()
    print("WebDriver closed.")

    # Parse the page source with BeautifulSoup
    try:
        print("Parsing HTML with BeautifulSoup...")
        soup = BeautifulSoup(page_source, "html.parser")
        print("HTML parsed successfully.")
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return []

    # Scrape the news items
    try:
        print("Searching for news items...")
        news_items = soup.find_all("a", class_="NwsLstPg_img")
        print(f"Found {len(news_items)} news items.")
    except Exception as e:
        print(f"Error finding news items: {e}")
        return []

    # Initialize list to store formatted entries
    formatted_entries = []

    # Process each news item
    for item in news_items:
        try:
            # Extract date and time
            date_time_element = item.find("span", class_="NwsLstPg_ovl-dt-nm")
            date_time = date_time_element.get_text(strip=True) if date_time_element else "N/A"

            # Extract headline from the <img> tag inside the <a> tag
            img_element = item.find("img", class_="NwsLstPg_img-full")
            headline = img_element.get("title", "N/A") if img_element else "N/A"

            # Extract link
            link = item["href"]

            # Extract image URL
            image_url = img_element.get("src", "N/A") if img_element else "N/A"

            # Generate a unique ID for each news item
            news_id = str(uuid.uuid4())

            # Use Groq API to extract location and crime type
            extracted_data = extract_location_and_crime_type(headline)
            location = extracted_data.get("location", "N/A")
            crime_type = extracted_data.get("crime_type", "N/A")

            # Format the entry as a dictionary
            formatted_entry = {
                "content": headline,  # Use headline as content
                "date": date_time.split()[0] + date_time.split()[1]+ date_time.split()[2],  # Extract date part
                "id": news_id,
                "imageUrl": image_url,
                "readMoreUrl": link,
                "time":date_time.split()[3] + date_time.split()[4],  
                "url": link,
                "type": crime_type,  # Crime type extracted using Groq API
                "location": location  # Location extracted using Groq API
            }

            # Append the formatted entry to the list
            formatted_entries.append(formatted_entry)

        except Exception as e:
            print(f"Error processing news item: {e}")

    # Return the formatted entries
    return {"data": formatted_entries}





# # Refined prompt using the Groq API
# def query_groq(file_type, context_str, user_query):
#     context = f"""
#     You are given a dictionery {context_str} containing crime records with the following columns:

#     Date: The date of the crime incident.
#     Headline: The headline of the crime news.
#     Link: The URL to the full news article.
    
#     YOUR TASK: Format the crime records in the following way:
#     [Date | Time] Crime Type – Location 
#     Brief description of the crime (extracted or inferred from the headline). Link: [URL]
    
#     IF YOU NOT FIND ANYTHING WRITE N/A. DO NOT WRITE ANY LOACTION OUTSIDE DELHI NCR AND NEWS SHOULD BE RELATED TO CRIME ONLY.

#     Examples:
#     1. **Extract Location and Crime Type**:
#        - Identify the location and crime type from the headline.
#        - Example: For the headline "Robbery in Connaught Place", the crime type is "Robbery" and the location is "Connaught Place".

#     2. **Format the Output**:
#        - Format each crime record as follows:
#          [Date | Time] Crime Type – Location
#          Brief description of the crime (extracted or inferred from the headline).
#          Link: [URL]

#     Output Format:
#     - [Date | Time] Crime Type – Location 
#     Brief description of the crime (extracted or inferred from the headline). Link: [URL]

#     Note: Ensure that the output is formatted correctly and includes the required information. NO OTHER OUTPUT SHOULD BE THERE.
#     """

#     try:
#         # Requesting completion from Groq API
#         response = client.chat.completions.create(
#             messages=[{"role": "user", "content": context}],
#             model="llama3-8b-8192"
#         )

#         # Accessing the message content correctly
#         result = response.choices[0].message.content

#         print(f"Processed Result: {result}")

#         return result

#     except Exception as e:
#         print(f"Error occurred while querying Groq API: {e}")
#         return "unknown; unknown"

# # Convert `data_dict` into a string for the Groq API
# context_str = "\n".join(data_dict["entries"])

# context_str = "\n".join(data_dict["entries"])

# # Query the Groq API to format the news
# formatted_output = query_groq(file_type="text", context_str=context_str, user_query="Format the crime records.")

# # Print the formatted output
# print("\nFormatted Output:")
# print(formatted_output)
