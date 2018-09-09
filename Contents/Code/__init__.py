import re
import random
import urllib
import urllib2 as urllib
import urlparse
import json
from datetime import datetime
from PIL import Image
from cStringIO import StringIO

VERSION_NO = '2.2018.09.08.1'

def any(s):
    for v in s:
        if v:
            return True
    return False

def Start():
    HTTP.ClearCache()
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'
    HTTP.Headers['Accept-Encoding'] = 'gzip'

def capitalize(line):
    return ' '.join([s[0].upper() + s[1:] for s in line.split(' ')])

def tagAleadyExists(tag,metadata):
    for t in metadata.genres:
        if t.lower() == tag.lower():
            return True
    return False

def posterAlreadyExists(posterUrl,metadata):
    for p in metadata.posters.keys():
        Log(p.lower())
        if p.lower() == posterUrl.lower():
            Log("Found " + posterUrl + " in posters collection")
            return True

    for p in metadata.art.keys():
        if p.lower() == posterUrl.lower():
            return True
    return False

class EXCAgent(Agent.Movies):
    name = 'Girlsway'
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']
    primary_provider = True

    def search(self, results, media, lang):
        
        title = media.name
        if media.primary_metadata is not None:
            title = media.primary_metadata.title
        title = title.replace("'","").replace('"','')
        Log('*******MEDIA TITLE****** ' + str(title))

        # Search for year
        year = media.year
        if media.primary_metadata is not None:
            year = media.primary_metadata.year
        title = title.replace("."," ").replace("(","").replace(")","")    
        encodedTitle = urllib.quote(title)
        
        Log(encodedTitle)
        searchResults = HTML.ElementFromURL('https://www.girlsway.com/en/search/' + encodedTitle)

        for searchResult in searchResults.xpath('//div[@class="tlcTitle"]'):

            Log(searchResult.text_content())
            titleNoFormatting = searchResult.xpath('.//a')[0].get("title")
            curID = searchResult.xpath('.//a')[0].get("href")
            curID = curID.replace('/','_')
            Log(str(curID))
            lowerResultTitle = str(titleNoFormatting).lower()
            score = 100 - Util.LevenshteinDistance(title.lower(), titleNoFormatting.lower())
            titleNoFormatting = titleNoFormatting + " [Girlsway]"
            results.Append(MetadataSearchResult(id = curID, name = titleNoFormatting, score = score, lang = lang))
                
        results.Sort('score', descending=True)            

    def update(self, metadata, media, lang):

        Log('******UPDATE CALLED*******')
        
        temp = str(metadata.id).replace('_','/')
        url = 'https://www.girlsway.com' + temp
        detailsPageElements = HTML.ElementFromURL(url)

        # Summary
        metadata.summary = detailsPageElements.xpath('//div[contains(@class,"sceneDesc")]')[0].text_content()[60:]
        metadata.title = detailsPageElements.xpath('//h1[@class="title"]')[0].text_content()
        metadata.studio = "Girlsway"
        date = detailsPageElements.xpath('//div[@class="updatedDate"]')[0].text_content()[14:24]
        Log(date)
        date_object = datetime.strptime(date, '%Y-%m-%d')
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year    
        
        # Genres
        metadata.genres.clear()
        genres = detailsPageElements.xpath('//div[contains(@class,"sceneColCategories")]//a')
        if len(genres) > 0:
            for genreLink in genres:
                genreName = genreLink.text_content().lower()
                metadata.genres.add(capitalize(genreName))

        # Actors
        metadata.roles.clear()
        actors = detailsPageElements.xpath('//div[contains(@class,"sceneColActors")]//a')
        if len(actors) > 0:
            for actorLink in actors:
                role = metadata.roles.new()
                actorName = actorLink.text_content()
                role.name = actorName
                actorPageURL = "https://www.girlsway.com" + actorLink.get("href")
                actorPage = HTML.ElementFromURL(actorPageURL)
                actorPhotoURL = actorPage.xpath('//img[@class="actorPicture"]')[0].get("src")
                role.photo = actorPhotoURL
        
        # Posters/Background
        posterURL = detailsPageElements.xpath('//meta[@name="twitter:image"]')[0].get("content")
        Log("PosterURL: " + posterURL)
        metadata.art[posterURL] = Proxy.Preview(HTTP.Request(posterURL, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
        metadata.posters[posterURL] = Proxy.Preview(HTTP.Request(posterURL, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
                