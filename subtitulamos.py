# -*- coding: utf-8 -*-
import logging
import re
import json

from babelfish import Language, language_converters
from guessit import guessit
from requests import Session

from . import ParserBeautifulSoup, Provider
from .. import __short_version__








class SubtitulamosSubtitle(Subtitle):
    """Subtitulamos.tv Subtitle."""
    provider_name = 'subtitulamos'
    
    def _init_(self, language, series, season, episode, title, version, download_link):
        super(SubtitulamosSubtitle, self)._init_(language)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.version = version
        self.download_link = download_link
        
    @property
    def id(self):
        return self.download_link
        
    def get_matches(self, video):
        matches = set()
        
        # series name
        if video.series and sanitize(self.series) in (
                sanitize(name) for name in [video.series] + video.alternative_series):
            matches.add('series')
        # season
        if video.season and self.season == video.season:
            matches.add('season')
        # episode
        if video.episode and self.episode == video.episode:
            matches.add('episode')
        # title of the episode
        if video.title and sanitize(self.title) == sanitize(video.title):
            matches.add('title')
        # release group
        if (video.release_group and self.version and
                any(r in sanitize_release_group(self.version)
                    for r in get_equivalent_release_groups(sanitize_release_group(video.release_group)))):
            matches.add('release_group')
        
        return matches
        
class SubtitulamosProvider(Provider):
    """Subtitulamos.tv Provider."""
    languages = {Language(l) for l in ['eng', 'spa', 'lat', 'cat']}
    video_types = (Episode,)
    server_url = 'http://www.subtitulamos.tv/'
    subtitle_class = SubtitulamosSubtitle
    
    def _init_(self):
        self.session = None
        
    def initialize(self):
        self.session = Session()
        self.session.headers['User-Agent'] = 'Subliminal/%s' % __short_version__
        
    def terminate(self):
        self.session.close()
        
    def get_show_id(self, series):
        params = {'q': series}
        logger.info('Getting show id')
        r = self.session.get(self.server_url + 'search/query',  params=params, timeout=10)
        r.raise_for_status()
        
        busqueda = r.content
        if not busqueda:
            logger.error('Show id not found')
            return None
        show_id = busqueda[0]['id']
        
        return show_id
        
    def query(self, show_id, series, season, episode): 
        # get the episode ids
        episode_ids = self.get_episode_ids(show_id, season)
        if episode not in episode_ids:
            logger.error('Episode %d not found', episode)
            return []

        # get the episode page
        logger.info('Getting the page for episode %d', episode_ids[episode])
        r = self.session.get(self.server_url + 'episodes/%d' % episode_ids[episode], timeout=10)
        soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])

        # loop over subtitles
        subtitles = []
        row = soup.select_one('.subtitle_language')
        while row.has_attr('class'):
            if row['class'][0] == 'subtitle_language':
                language = Language.fromsubtitulamos(row.text)
            if row['class'][0] == 'compact':
                versiones = row.select_one('.version_name').text.split('/')
                completado = 
       
        
        
            row = row.find_next_sibling('div')
        
        
        
    def list_subtitles(self, video, languages):
        # lookup show_id
        show_id = self.get_show_id(video.series)

        if show_id is not None:
            subtitles = [s for s in self.query(show_id, video.series, video.season, video.episode)
                         if s.language in languages]
            if subtitles:
                return subtitles
        else:
            logger.error('No show id found for %r', video.series)

        return []

    def download_subtitle(self, subtitle):
        # donwload the subtitle
        logger.info('Downloading subtitle %r', subtitle)
        r = self.session.get(self.server_url + subtitle.download_link, timeout=10)
        r.raise_for_status()
        
        if not r.content:
            logger.debug('Unable to download subtitle. No data returned from provider')
            return
        
        subtitle.content = fix_line_endings(r.content)