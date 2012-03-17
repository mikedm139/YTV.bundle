NAME = "YTV"
ART  = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = "http://www.ytv.com/videos/"
YTV_PLAYER_KEY = "AQ~~,AAAAocwuf3E~,OkU0MlqQwrSzQO2jTf7KgSe64XrUuKHP"
YTV_PLAYER_ID = "912499644001"
AMF_URL = 'http://c.brightcove.com/services/messagebroker/amf'

####################################################################################################
def Start():

    Plugin.AddPrefixHandler("/video/ytv", VideoMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "List"
    MediaContainer.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def VideoMainMenu():

    dir = MediaContainer(viewGroup="InfoList")

    page = HTML.ElementFromURL(BASE_URL)
    categories = []

    for category in page.xpath('//div[@id="video-navigation"]//a'):
        title = category.text
        url = category.get('href')
        if  url == '/videos/': url = '?'
        if title.lower() in categories:
            continue
        else:
            dir.Append(Function(DirectoryItem(CategoryPage, title=title), url=url))
            categories.append(title.lower())

    dir.Sort('title')

    return dir

####################################################################################################
def CategoryPage(sender, url):

    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)

    request_url = BASE_URL + 'videos.ashx' + url
    results = JSON.ObjectFromURL(request_url)

    for video in results:
        title = video['Name']
        summary = video['ShortDescription']
        thumb = video['ThumbnailURL']
        duration = (int(video['Duration'].split(":")[0])*60 + int(video['Duration'].split(":")[1]))*1000
        videoId = video['Id']
        dir.Append(Function(WebVideoItem(PlayVideo, title=title, duration=duration, summary=summary, thumb=Function(GetThumb, url=thumb)), videoId=videoId))

    return dir

####################################################################################################
def PlayVideo(sender, videoId):

    video = AmfRequest(playerID=YTV_PLAYER_ID, playerKey=YTV_PLAYER_KEY, videoPlayer=videoId)
    #video_url = video['FLVFullLengthURL']
    video_url = video['IOSRenditions'][0]['defaultURL']

    if video_url.startswith('rtmp'):
        (url, clip) = video_url.split('&', 1)
        clip = clip.strip('.mp4')
        return RTMPVideoItem(url, clip)

    return Redirect(video_url)

####################################################################################################
def GetThumb(url):

    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpeg')
    except:
        return Redirect(R(ICON))

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
