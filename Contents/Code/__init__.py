TITLE = 'Kijk'
API_BASE_URL = 'http://api.kijk.nl/v1/default/sections'
EPISODE_URL = 'http://www.npo.nl/redirect/00-00-0000/%s'
DAY = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
MONTH = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december']

####################################################################################################
def Start():

	ObjectContainer.title1 = TITLE
	HTTP.CacheTime = 300
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'

####################################################################################################
@handler('/video/kijk', TITLE)
def MainMenu():

	oc = ObjectContainer()

	oc.add(DirectoryObject(key=Callback(Overview, title='Populair', path='popular_PopularVODs?offset=0'), title='Populair'))
	oc.add(DirectoryObject(key=Callback(Overview, title='Series', path='episodes/popular.json'), title='Series'))
	oc.add(DirectoryObject(key=Callback(AZ), title='Programma\'s A-Z'))
	oc.add(DirectoryObject(key=Callback(OnDemand), title='Gemist'))

	return oc

####################################################################################################
@route('/video/kijk/overview')
def Overview(title, path):

	oc = ObjectContainer(title2=title)
	json_obj = JSON.ObjectFromURL('%s/%s' % (API_BASE_URL, path))
	episodes = []

	for video in json_obj['items']:

		title = video['title']
        summary = video['synopsis']
        episode_id = video['id']
        slug = video['format']
        channel = video['channel']

        thumbs = []
        if video['images']: thumbs.append(video['images']['retina_image'])

        broadcasted_at = video['date']

		episodes.append({
			'episode_id': episode_id,
			'slug': slug,
			'channel': channel,
			'title': title,
			'summary': summary,
			'thumbs': thumbs,
			'broadcasted_at': broadcasted_at
		})

	episodes = sorted(episodes, key=lambda k: k['broadcasted_at'], reverse=True)

	for episode in episodes:

		oc.add(DirectoryObject(
			key = Callback(Episode, slug=episode['slug'], channel=episode['channel'], episode_id=episode['episode_id']),
			title = episode['title'],
			summary = episode['summary'],
			thumb = Resource.ContentsOfURLWithFallback(episode['thumbs'])
		))

	return oc

####################################################################################################
@route('/video/kijk/episode/{slug}/{channel}/{episode_id}')
def Episode(slug, channel, episode_id):

	video = JSON.ObjectFromURL('https://api.kijk.nl/v1/default/pages/series-%s.%s-episode-%s' % (slug, channel, episode_id))

	oc = ObjectContainer(title2=video['title'])

	airdate = Datetime.FromTimestamp(video['sections'][0]['items'][0]['date'])
	title = video['sections'][0]['items'][0]['title']
	#title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

	thumbs = []
	if video['sections'][0]['items'][0]['images']: thumbs.append(video['sections'][0]['items'][0]['images']['retina_image')

	oc.add(VideoClipObject(
		url = EPISODE_URL % (video['sections'][0]['items'][0]['id']),
		title = title,
		summary = video['sections'][0]['items'][0]['synopsis'],
		duration = video['sections'][0]['items'][0]['durationSeconds'] * 60,
		originally_available_at = airdate.date(),
		thumb = Resource.ContentsOfURLWithFallback(thumbs)
	))

	#oc.add(DirectoryObject(
	#	key = Callback(Series, series_id=video['series']['id']),
	#	title = 'Alle afleveringen'
	#))

	return oc

####################################################################################################
@route('/video/kijk/series/{series_id}')
def Series(series_id):

	json_obj = JSON.ObjectFromURL('%s/series/%s.json' % (API_BASE_URL, series_id))

	oc = ObjectContainer(title2=json_obj['name'])

	for video in json_obj['episodes']:

		airdate = Datetime.FromTimestamp(video['broadcasted_at'])
		title = video['name'] if video['name'] else json_obj['name']
		title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

		thumbs = []
		if video['image']: thumbs.append(video['image'])
		if 'stills' in video and video['stills']: thumbs.append(video['stills'][0]['url'])
		if json_obj['image']: thumbs.append(json_obj['image'])

		oc.add(VideoClipObject(
			url = EPISODE_URL % (video['mid']),
			title = title,
			summary = video['description'],
			duration = video['duration'] * 1000,
			originally_available_at = airdate.date(),
			thumb = Resource.ContentsOfURLWithFallback(thumbs)
		))

	return oc

####################################################################################################
@route('/video/kijk/ondemand')
def OnDemand():

	oc = ObjectContainer(title2='Gemist')
	delta = Datetime.Delta(days=1)
	today = Datetime.Now()
	yesterday = (Datetime.Now() - delta)

	oc.add(DirectoryObject(key=Callback(Overview, title='Laatst toegevoegd', path='missed-all-%s?limit=250&offset=0' % (today.strftime('%Y%m%d'))), title='Laatst toegevoegd'))
	oc.add(DirectoryObject(key=Callback(Overview, title='Gisteren', path='missed-all-%s?limit=250&offset=0' % (yesterday.strftime('%Y%m%d'))), title='Gisteren'))

	for i in range(2, 10):

		date_object = Datetime.Now() - (delta * i)
		title = '%s %s %s' % (DAY[date_object.weekday()], date_object.day, MONTH[date_object.month])

		oc.add(DirectoryObject(key=Callback(Overview, title=title, path='missed-all-%s?limit=250&offset=0' % (date_object.strftime('%Y%m%d'))), title=title))

	return oc

####################################################################################################
@route('/video/kijk/az')
def AZ():

	oc = ObjectContainer(title2='Programma\'s A-Z')

	json_obj = JSON.ObjectFromURL('%s/programs-abc-0123456789abcdefghijklmnopqrstuvwxyz?limit=500&offset=0' % (API_BASE_URL))

	for programme in json_obj['items']:

		oc.add(DirectoryObject(
			key = programme['id'],
			title = programme['title'],
			summary = programme['synopsis'],
			thumb = Resource.ContentsOfURLWithFallback(programme['images']['retina_image'])
		))

	return oc
