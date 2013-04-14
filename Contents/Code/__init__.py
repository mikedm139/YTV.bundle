VIDEO_PREFIX = "/video/ytv"
NAME = "YTV"
ART  = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = "http://www.ytv.com"
EXCLUSIONS = ['http://www.ytv.com/shows/98/big-fun-movies/kidschoiceweekend.aspx']

NAMESPACES = {"plmedia" : "http://xml.theplatform.com/media/data/Media"}
SMIL_NS = {"a" : "http://www.w3.org/2005/SMIL21/Language"}

####################################################################################################

def Start():
    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    
####################################################################################################
@handler(VIDEO_PREFIX, NAME, ICON, ART)
def MainMenu():
    oc = ObjectContainer()
    page = HTML.ElementFromURL(BASE_URL)
    categories = []

    for category in page.xpath('//div[@class="mega-nav-item"]'):
        title = category.xpath('./a')[1].text.strip()
        url = category.xpath('./a')[1].get('href')
        if url in EXCLUSIONS:
            continue
        thumb = category.xpath('.//img')[0].get('src')
        if  url == '/videos/': url = '?'
        if title.lower() in categories:
            continue
        else:
            oc.add(DirectoryObject(key=Callback(CategoryPage, title=title, url=url), title=title, thumb=Resource.ContentsOfURLWithFallback(thumb)))
            categories.append(title.lower())

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
@route(VIDEO_PREFIX + "/category")
def CategoryPage(title, url):
    oc = ObjectContainer(title2=title)
    
    if url.startswith('http://'):
        request_url = url + 'watch.ashx'
    else:
        request_url = BASE_URL + url + 'watch.aspx'
    
    try:
        Log(request_url)
        data = HTML.ElementFromURL(request_url)
        platform_url = data.xpath('//div[@class="video-container"]//iframe')[0].get('src')
    except:
        request_url = request_url.replace('/watch.aspx', '/videos.aspx')
        Log(request_url)
        data = HTML.ElementFromURL(request_url)
        platform_url = data.xpath('//div[@class="video-container"]//iframe')[0].get('src')
    
    platform_data = HTML.ElementFromURL(platform_url)
    feed_url = platform_data.xpath('//link[@rel="alternate"]')[0].get('href')
    
    feed = RSS.FeedFromURL(feed_url)
    
    for item in feed.entries:
        url = item.link
        Log(url)
        title = item.title
        Log(title)
        summary = item.summary
        Log(summary)
        thumb = item.plmedia_defaultthumbnailurl
        Log(thumb)
        date = item.updated
        Log(date)
        duration = item.media_content[0]['duration']
        Log(duration)
        duration = int(float(duration)*1000)
        Log(duration)
        i = 0
        resolutions = []
        while i < len(item.media_content):
            bitrate = int(item.media_content[i]['bitrate'].split('.')[0])
            Log(bitrate)
            resolution = item.media_content[i]['height']
            Log(resolution)
            url = item.media_content[i]['url']
            Log(url)
            resolutions.append({'url':url, 'res':resolution, 'bitrate':bitrate})
            i += 1
        
        oc.add(CreateVideoClipObject(
            url = url,
            title = title,
            summary = summary,
            date = date,
            thumb = thumb,
            json_string = JSON.StringFromObject(resolutions)
    ))
    return oc

def CreateVideoClipObject(url, title, summary, date, thumb, json_string, include_container=False):
    items = []
    for version in JSON.ObjectFromString(json_string):
        items.append(
            MediaObject(
                parts = [PartObject(key=Callback(PlayVideo, url=version['url']))],
                bitrate = version['bitrate'],
                video_resolution = version['res'],
                audio_channels = 2,
                optimized_for_streaming = True
                )
            )

    items.reverse()

    videoclip_obj = VideoClipObject(
        key = Callback(CreateVideoClipObject, url=url, title=title, summary=summary, date=date, thumb=thumb, json_string=json_string, include_container=True),
        rating_key = url,
        title = title,
        summary = summary,
        thumb = Resource.ContentsOfURLWithFallback(thumb),
        items = items
    )

    if include_container:
        return ObjectContainer(objects=[videoclip_obj])
    else:
        return videoclip_obj
    
def PlayVideo(url):
    smil = XML.ElementFromURL(url + '&manifest=f4m&format=SMIL')
    video_url = smil.xpath('//a:video', namespaces = SMIL_NS)[0].get('src')
    headers = HTTP.Request(video_url).headers
    Log(headers)
    return Redirect(video_url)