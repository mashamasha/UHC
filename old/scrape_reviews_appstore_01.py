import json
import os
import requests
import sys
import xmltodict

from collections import Counter


def fetch_reviews(app_id, country = 'us', sortBy = 'mostRecent', page = 1):
    """ Get max 500 user reviews for a given app.
    
    app_id = ID number of application.
    country = default to United States (us).
    sorty = 'mostRecent'(default) or 'mostHelpful'.
    page = page number. default = 1, max = 10.
    """
    
    url = 'https://itunes.apple.com/%s/rss/customerreviews/id=%s/sortBy=%s/page=%s/xml' % (country, 
                                                                                           str(app_id), 
                                                                                           sortBy,
                                                                                           str(page))
    r = requests.get(url)

    try:  # If there are no reviews on this page or is a broken xml, return empty list
        reviews_dict = xmltodict.parse(r.text)
        reviews_list = reviews_dict['feed']['entry']
    except:
        return []
    
    reviews = []
    for review in reviews_list:  # Gather data from each review and put into a list.
        try:
            reviews.append({'title': review['title'],
                           'author': review['author']['name'],
                           'authorUrl': review['author']['uri'],
                           'rating': review['im:rating'],
                           'date': review['updated'],
                           'voteSum': review['im:voteSum'],
                           'voteCount': review['im:voteCount'],
                           'content': review['content'][0]['#text'].replace('\n', ' ')
                          })
        except:
            continue

    return reviews


def fetch_apps(terms: list, limit: int):
    """Uses the iTunes store search API to get metadata for apps.
    
    terms: A list of terms to search (ie. ["Medical", "Personal", "Health"])
    limit: Number of apps to return (max 200)
    """
    
    url = "https://itunes.apple.com/search?media=software&entity=software" \
        "&term=%s&limit=%s" % ("+".join(terms),
                               limit)
            
    r = requests.get(url)
    return r.text


if __name__ == "__main__":
    apps = fetch_apps(["Medical", "Personal", "Information"], 200)

    #filtered_apps = [ app for app in apps['results'] 
    #                 if app['primaryGenreName'] == 'Health & Fitness' ] # Filter out all non-Health&Fitness apps.

    app_metadata = []

    for app in apps:
        # Get app metadata
        print(app['trackName'])
        try:
            app_data = {'name': app['trackName'],
                        'id': app['trackId'],
                        'url': app['trackViewUrl'],
                        'price': app['price'],
                        'avgUserRating': app['averageUserRating'],
                        'userRatingCount': app['userRatingCount'],
                        'currentVersionReleaseDate': app['currentVersionReleaseDate'],
                        'description': app['description'].replace('\n', ' ')
                        }
        except:
            continue
        
        # Get most recent and most helpful reviews (separately) for app (up to 500)
        # NOTE: If the app does not have many reviews, the same reviews may be included in both recent
        # and helpful reviews.
        recent_reviews = []
        helpful_reviews = []
        for i in range(1, 11): 
            print(i)
            recent_reviews += fetch_reviews(app_data['id'], page=i)
            helpful_reviews += fetch_reviews(app_data['id'], sortBy='mostHelpful', page=i)

        app_data['recent_reviews'] = recent_reviews
        app_data['helpful_reviews'] = helpful_reviews
        app_metadata.append(app_data)

    with open('appstore_metadata_and_reviews_health+personal+information_200.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(app_metadata, ensure_ascii=False))

    print("DONE!")
