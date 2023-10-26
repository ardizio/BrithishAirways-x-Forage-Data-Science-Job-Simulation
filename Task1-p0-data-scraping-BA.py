import requests
from bs4 import BeautifulSoup
import csv
import os
import uuid
import re
import pandas as pd



def list_files_in_folder(folder_path):
    #file_names = list_files_in_folder('/Users/admin/Desktop/Forage/British Airways/data')
    #print(file_names[2])
    file_names = []    
    # List all files in the folder
    for files in os.walk(folder_path):
        for file in files:
            file_names.append(file)
    
    return file_names

def download_BA_airlinequality(pages = 37, page_size = 100):
    base_url = "https://www.airlinequality.com/airline-reviews/british-airways"
    # for i in range(1, pages + 1):
    for i in range(1, pages + 1):
        print(f"Scraping page {i}")
        # Create URL to collect links from paginated data
        url = f"{base_url}/page/{i}/?sortby=post_date%3ADesc&pagesize={page_size}"
        # Collect HTML data from this page
        response = requests.get(url)
        # Parse content
        content = response.content

        save_data_to_file(f'airlinequality_{i}_{page_size}','html',content)

def save_data_to_file(name, file_type, content):
    # Generate a unique filename based on UUID
    # unique_filename = f"{name}-{uuid.uuid4()}.{file_type}"
    unique_filename = f"{name}.{file_type}"
    # Define the path to the 'data' directory in the current working directory
    data_directory = os.path.join(os.getcwd(), 'data')

    # Define the path to the save directory
    file_path = os.path.join(data_directory, unique_filename)

    content =  str(content)
    # Check if the file already exists
    if os.path.exists(file_path):
        # If the file exists, append the data to it
        with open(file_path, 'a') as file:
            file.write(content)
    else:
        # If the file doesn't exist, create a new file and save the data
        with open(file_path, 'w') as file:
            file.write(content)

def split_route_string(route_string):
    # Initialize variables
    route_from = ""
    route_via = "direct"
    route_to = ""

    # Split the string into words
    words = route_string.split()

    # Find the index of "to" and "via" keywords
    to_index = words.index("to") if "to" in words else False
    via_index = words.index("via") if "via" in words else False

    if to_index!= False and via_index!=False and to_index<via_index:
        part = route_string.split(' to ')
        route_from =  part[0]
        second = part[1].split(' via ')
        route_to = second[0]
        route_via  = second[1]
    elif to_index!= False and via_index!=False and to_index>via_index:
        part = route_string.split(' via ')
        route_from =  part[0]
        second = part[1].split(' to ')
        route_via = second[0]
        route_to  = second[1]
    elif to_index!= False:
        part = route_string.split(' to ')
        route_from =  part[0]
        route_to = part[1]
    elif via_index!= False:
        part = route_string.split(' via ')
        route_to =  part[0]
        route_via = "via"
        route_from = part[1]

    return route_from, route_via, route_to

def parser(html_data_path, csv_file_path):
    # Read the HTML content from the file
    with open(html_data_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    parserHadToExtract = True
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all the articles with the specified itemprop attribute
    articles = soup.find_all("article", itemprop="review")

    # Create a list to store extracted data from multiple items
    data_list = []

    # Iterate through the articles and extract the desired data
    for article in articles:
        # if ACTIVE parser
        if parserHadToExtract == True:
            
            # get review ratin 1 to 10
            # Get rating or replace with 'u' if not found
            rating_element = article.find("span", itemprop="ratingValue")
            rating = rating_element.get_text() if rating_element else 'u'

            # Get author name or replace with 'u' if not found
            author_element = article.find("span", itemprop="name")
            author = author_element.get_text() if author_element else 'u'

            # get published date
            date_published = article.find("time", itemprop="datePublished")["datetime"]

            #get review title
            h2_element = article.find("h2", class_="text_header")
            if h2_element:
                review_title = h2_element.get_text()
                review_title = review_title.replace('"', '')
            else:
                review_title = ""

            # Extract Review_Validity and Review_text (main body)
            review_body = article.find("div", itemprop="reviewBody")
            if review_body:
                review_text = review_body.get_text()
                # Split the review_text by the first '|'
                split_review = review_text.split('|', 1)
                first_part = split_review[0].strip()

                # Check if the first part contains "Trip Verified"
                trip_verified = "Trip Verified" in first_part

                if len(split_review) > 1:
                    # Extract and process the review text
                    review_text = split_review[1].strip()
                    review_text = review_text.replace("\xc2\xa0", " ")  # Replace non-breaking spaces
                    review_text = review_text.lstrip()
                else:
                    review_text = ""
            else:
                # Handle the case where the review body is not found
                trip_verified = False
                review_text = ""

            # get review ID
            div_with_id = article.find("div", class_="body")
            if div_with_id:
                review_id = div_with_id.get("id")
                review_id = review_id.replace('anchor', '')
            else:
                review_id = ''

            # get author Nationality
            time_element = article.find('time', itemprop="datePublished")
            if time_element:
                # Get the previous sibling element (which should be the country element in parentheses)
                country_element = time_element.find_previous_sibling(string=re.compile(r'\(.*\)'))
                if country_element:
                    # Extract the text from the country element
                    author_nationality = country_element.strip('() ')
                    index_of_open_parenthesis = author_nationality.find('(')
                    # Remove everything before the first '('
                    if index_of_open_parenthesis != -1:
                        author_nationality = author_nationality[index_of_open_parenthesis:]
                        author_nationality = author_nationality.replace('(', '')
                else:
                    author_nationality = ""
            else:
                author_nationality = ""

            # Access Table Keys
            type_of_traveller = ''
            aircraft = ''
            cabin_flown = ''
            route_from = ''
            route_via = ''
            route_to = ''
            date_flown_month = ''
            date_flown_year = ''
            seat_comfort = 'u'
            cabin_staff_service = 'u'
            food_and_beverages = 'u'
            inflight_entertainment = 'u'
            ground_service = 'u'
            wifi_and_connectivity = 'u'
            value_for_money = 'u'
            recommendation = 'u'
            table_element = article.find("table", class_="review-ratings")
            if table_element:
                tr_elements = table_element.find_all("tr")
                for tr in tr_elements:
                    td_elements = tr.find_all("td")                        
                    for td_element in td_elements:
                        to_str_td = str(td_element)
                        if 'type_of_traveller' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                type_of_traveller = next_td.get_text()
                        elif 'aircraft' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                aircraft = next_td.get_text()
                        elif 'cabin_flown' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                cabin_flown = next_td.get_text()
                        elif 'route' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                route = next_td.get_text()
                                route_from, route_via, route_to = split_route_string(route)
                        elif 'date_flown' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                date_flown = next_td.get_text()
                                date_flown = date_flown.split(' ')
                                date_flown_month = date_flown[0]
                                date_flown_year = date_flown[1]
                        elif 'seat_comfort' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                seat_comfort = str(next_td)
                                seat_comfort = seat_comfort.split('fill')
                                num_split_items = len(seat_comfort)
                                seat_comfort = seat_comfort[num_split_items-1]
                                seat_comfort = seat_comfort[2]
                        elif 'cabin_staff_service' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                cabin_staff_service = str(next_td)
                                cabin_staff_service = cabin_staff_service.split('fill')
                                num_split_items = len(cabin_staff_service)
                                cabin_staff_service = cabin_staff_service[num_split_items-1]
                                cabin_staff_service = cabin_staff_service[2]
                        elif 'food_and_beverages' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                food_and_beverages = str(next_td)
                                food_and_beverages = food_and_beverages.split('fill')
                                num_split_items = len(food_and_beverages)
                                food_and_beverages = food_and_beverages[num_split_items-1]
                                food_and_beverages = food_and_beverages[2]
                        elif 'inflight_entertainment' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                inflight_entertainment = str(next_td)
                                inflight_entertainment = inflight_entertainment.split('fill')
                                num_split_items = len(inflight_entertainment)
                                inflight_entertainment = inflight_entertainment[num_split_items-1]
                                inflight_entertainment = inflight_entertainment[2]
                        elif 'ground_service' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                ground_service = str(next_td)
                                ground_service = ground_service.split('fill')
                                num_split_items = len(ground_service)
                                ground_service = ground_service[num_split_items-1]
                                ground_service = ground_service[2]
                        elif 'wifi_and_connectivity' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                wifi_and_connectivity = str(next_td)
                                wifi_and_connectivity = wifi_and_connectivity.split('fill')
                                num_split_items = len(wifi_and_connectivity)
                                wifi_and_connectivity = wifi_and_connectivity[num_split_items-1]
                                wifi_and_connectivity = wifi_and_connectivity[2]
                        elif 'value_for_money' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                value_for_money = str(next_td)
                                value_for_money = value_for_money.split('fill')
                                num_split_items = len(value_for_money)
                                value_for_money = value_for_money[num_split_items-1]
                                value_for_money = value_for_money[2]
                        elif 'recommended' in to_str_td:
                            next_td = td_element.find_next("td")
                            if next_td:
                                recommendation = next_td.get_text()

            

            # Define the list of variables
            vrs = [review_id, rating, author, author_nationality, trip_verified, review_title, date_published, review_text, type_of_traveller, aircraft, cabin_flown, route_from, route_via, route_to, date_flown_month, date_flown_year, seat_comfort, cabin_staff_service, food_and_beverages, inflight_entertainment, ground_service, wifi_and_connectivity, value_for_money, recommendation]

            # Convert the list of variables to a delimited string
            line_to_append = '%%%'.join(map(str, vrs)) + '%%%'

            # Append the line to the existing CSV file
            with open(csv_file_path, mode="a", newline="") as csv_file:
                csv_file.write(line_to_append + '\n')


            """ data_list.append({
                "id": review_id,
                "rating": rating,
                "author": author,
                "authorNationality": author_nationality,
                "isTripVerified": trip_verified,
                "title": review_title,
                "datePublished": date_published,
                "body": review_text,
                "travellerType": type_of_traveller,
                "aircraft":aircraft,
                "cabin":cabin_flown,
                "routeFrom":route_from,
                "routeVia":route_via,
                "routeTo":route_to,
                "dateFlownMonth":date_flown_month,
                "dateFlownYear":date_flown_year,
                "ratingSeatComfort":seat_comfort,
                "ratingCabinStaffService":cabin_staff_service,
                "ratingFoodAndBeverages":food_and_beverages,
                'ratingInflightEntertainment':inflight_entertainment,
                'ratingGroundService':ground_service,
                'ratingWifiAndConnectivity': wifi_and_connectivity,
                'ratingValueForMoney': value_for_money,
                'airlineRecommendation': recommendation
            }) """

        # else STOPPED parser
        else:
            #Extracting all possibles review-rating-heade -> keys
            table_element = article.find("table", class_="review-ratings")
            extracted_values = []
            if table_element:
                tr_elements = table_element.find_all("tr")
                for tr in tr_elements:
                    td_elements = tr.find_all("td")                        
                    for td_element in td_elements:
                        to_str_td = str(td_element)
                        parts = to_str_td.split("review-rating-header")
                        if len(parts) > 1:
                            result = parts[1]
                            parts = result.split('"')
                            result = parts[0]
                            result = result[1:]
                            if result not in extracted_values:
                                extracted_values.append(result) 

        #print("\n\n\n\n\n")    

    """ if extracted_values:
        print(extracted_values) """
    """ if data_list:
        first_dict = data_list[0]
        print("-------Item-------")
        # Display each key and its corresponding value in the first dictionary
        for key, value in first_dict.items():
            print(f"{key}: {value}")
    else:
        print("No data found in data_list.") """
    

def createCSV():
    column_names = [
    "id",
    "rating",
    "author",
    "authorNationality",
    "isTripVerified",
    "title",
    "datePublished",
    "body",
    "travellerType",
    "aircraft",
    "cabin",
    "routeFrom",
    "routeVia",
    "routeTo",
    "dateFlownMonth",
    "dateFlownYear",
    "ratingSeatComfort",
    "ratingCabinStaffService",
    "ratingFoodAndBeverages",
    'ratingInflightEntertainment',
    'ratingGroundService',
    'ratingWifiAndConnectivity',
    'ratingValueForMoney',
    'airlineRecommendation']

    # Specify the file path where you want to save the CSV file (in the "data" subdirectory)
    csv_file_path = "data/t1p0-dataset_scraped_airlinequality_BA.csv"

    # Create the "data" subdirectory if it doesn't exist
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    # Check if the file already exists, and delete it if it does
    if os.path.exists(csv_file_path):
        os.remove(csv_file_path)

    # Create the CSV file and write the header row
    with open(csv_file_path, mode="w", newline="") as csv_file:
        # Write the header row enclosed within "%%%"
        header_row = '%%%'.join(column_names) + '%%%\n'
        csv_file.write(header_row)

    for i in range(1, 38):
        line = f'data/airlinequality_{i}_100.html'
        parser(line, csv_file_path)
        print(f'Handling LINE {i}')


#-------------MAIN----------------------#
#createCSV()




#ARTICLE CORPUR PRETTIFIED: 
#XXX stands for data extration successful
'''
<article itemprop="review" itemscope="" itemtype="http://schema.org/Review" class="comp comp_media-review-rated list-item media position-content review-877425">
    <meta itemprop="datePublished" content="2023-10-21">XXX
        <div itemprop="reviewRating" itemscope="" itemtype="http://schema.org/Rating" class="rating-10">
            <span itemprop="ratingValue">XXX</span>/<span itemprop="bestRating">10</span>
        </div>
        <div class="body" id="anchor877425">XXX
            <h2 class="text_header">"even Ryanair have more space"</h2>XXX
            <h3 class="text_sub_header userStatusWrapper">
            <span itemprop="author" itemscope="" itemtype="http://schema.org/Person">
                <span itemprop="name">XXX</span>
            </span> 
            (Netherlands) XXX
            <time itemprop="datePublished" datetime="2023-10-21">21st October 2023</time></h3>

            <div class="tc_mobile">
                XXX<div class="text_content " itemprop="reviewBody"><strong><a href="https://www.airlinequality.com/verified-reviews/"><em>Not Verified</em></a></strong> | Cabin luggage had to go to cargo, even when I said I carried medicines. There was no time to get them out the hand luggage. The economy seats with Virgin Atlantic, KLM and even Ryanair have more space. Luckily it was a short flight.</div>
                    
                    <div class="review-stats">                                           
                        <table class="review-ratings"><tbody><tr>
                            <td class="review-rating-header type_of_traveller ">Type Of Traveller</td>
                            <td class="review-value ">Solo Leisure</td>
                        </tr><tr>
                            <td class="review-rating-header cabin_flown ">Seat Type</td>
                            <td class="review-value ">Economy Class</td>
                        </tr><tr>
                            <td class="review-rating-header route ">Route</td>
                            <td class="review-value ">London to Amsterdam</td>
                        </tr><tr>
                            <td class="review-rating-header date_flown ">Date Flown</td>
                            <td class="review-value ">October 2023</td>
                        </tr><tr><td class="review-rating-header seat_comfort">Seat Comfort</td><td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td></tr><tr><td class="review-rating-header cabin_staff_service">Cabin Staff Service</td><td class="review-rating-stars stars"><span class="star fill">1</span><span class="star fill">2</span><span class="star fill">3</span><span class="star">4</span><span class="star">5</span></td></tr><tr><td class="review-rating-header ground_service">Ground Service</td><td class="review-rating-stars stars"><span class="star fill">1</span><span class="star fill">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td></tr><tr><td class="review-rating-header value_for_money">Value For Money</td><td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td></tr><tr>
                            <td class="review-rating-header recommended">Recommended</td>
                            <td class="review-value rating-no">no</td>
                        </tr>
                    </tbody></table>                   
                </div>

            </div>
        </div>
    <a href="#anchor877425" class="toggle-click tc_mobile_only"></a>     
</article>
'''

 
#REVIEWS TABLE:
#GO TO: searc with control+f the following
#Extracting all possibles review-rating-heade -> keys
'''
EXTRACTED KEYWORDS
review_table_keys = ['type_of_traveller', 'cabin_flown', 'route', 'date_flown', 'seat_comfort', 'cabin_staff_service', 'food_and_beverages', 'inflight_entertainment', 'ground_service', 'wifi_and_connectivity', 'value_for_money', 'recommended']

<class 'bs4.element.Tag'>
<td class="review-rating-header type_of_traveller">Type Of Traveller</td>
<td class="review-value">Couple Leisure</td>
<td class="review-rating-header cabin_flown">Seat Type</td>
<td class="review-value">Premium Economy</td>
<td class="review-rating-header route">Route</td>
<td class="review-value">Chicago to Rome via London</td>
<td class="review-rating-header date_flown">Date Flown</td>
<td class="review-value">July 2023</td>
<td class="review-rating-header seat_comfort">Seat Comfort</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star fill">2</span><span class="star fill">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header cabin_staff_service">Cabin Staff Service</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header food_and_beverages">Food &amp; Beverages</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header inflight_entertainment">Inflight Entertainment</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header ground_service">Ground Service</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header wifi_and_connectivity">Wifi &amp; Connectivity</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header value_for_money">Value For Money</td>
<td class="review-rating-stars stars"><span class="star fill">1</span><span class="star">2</span><span class="star">3</span><span class="star">4</span><span class="star">5</span></td>
<td class="review-rating-header recommended">Recommended</td>
<td class="review-value rating-no">no</td>
'''