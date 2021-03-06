VIDEO_PREFIX = "/video/ytv"
NAME = "YTV"
ART  = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = "http://www.ytv.com/videos/"
YTV_PLAYER_KEY = "AQ~~,AAAAocwuf3E~,OkU0MlqQwrSzQO2jTf7KgSe64XrUuKHP"
YTV_PLAYER_ID = "912499644001"
AMF_URL = 'http://c.brightcove.com/services/messagebroker/amf'

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

    for category in page.xpath('//div[@id="video-navigation"]//a'):
        title = category.text
        url = category.get('href')
        if  url == '/videos/': url = '?'
        if title.lower() in categories:
            continue
        else:
            oc.add(DirectoryObject(key=Callback(CategoryPage, title=title, url=url), title=title))
            categories.append(title.lower())

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
@route(VIDEO_PREFIX + "/category")
def CategoryPage(title, url):
    oc = ObjectContainer(title2=title)

    request_url = BASE_URL + 'videos.ashx' + url
    results = JSON.ObjectFromURL(request_url)

    for video in results:
        title = video['Name']
        summary = video['ShortDescription']
        thumb = video['ThumbnailURL']
        duration = (int(video['Duration'].split(":")[0])*60 + int(video['Duration'].split(":")[1]))*1000
        videoId = video['Id']
        Log(videoId)
        url = "YTV_PLUGIN://videoID=%s" % videoId
        oc.add(
            VideoClipObject(
                url = url,
                title = title,
                summary = summary,
                duration = duration, 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            )
        )

    return oc

####################################################################################################
def AmfRequest(playerID=None, playerKey=None, videoPlayer=None):

    endpoint = AMF_URL
    if playerKey:
        endpoint += '?playerKey=%s' % playerKey

    client = AMF.RemotingService(url=endpoint, user_agent='', client_type=3)
    service = client.getService('com.brightcove.experience.ExperienceRuntimeFacade')

    AMF.RegisterClass(ContentOverride, 'com.brightcove.experience.ContentOverride')
    AMF.RegisterClass(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')

    video_obj = ContentOverride(videoPlayer)
    experience = ViewerExperienceRequest(playerID, playerKey, video_obj)

    return service.getDataForExperience('', experience)['programmedContent']['videoPlayer']['mediaDTO']

####################################################################################################
class ContentOverride(object):
  def __init__ (self, videoPlayer=None):
    self.contentType = int(0)
    self.contentIds = None
    self.target = 'videoPlayer'
    self.contentId = int(videoPlayer)
    self.featuredRefId = None
    self.contentRefIds = None
    self.featuredId = float('nan')
    self.contentRefId = None

class ViewerExperienceRequest(object):
  def __init__ (self, playerID=None, playerKey=None, video_obj=None):
    self.experienceId = int(playerID)
    self.playerKey = playerKey
    self.contentOverrides = []
    self.contentOverrides.append(video_obj)
    self.TTLToken = ''
    self.URL = ''
    self.deliveryType = float('nan')
