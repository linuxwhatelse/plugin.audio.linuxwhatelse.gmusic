from gmusicapi.protocol.mobileclient import *

sj_url = 'https://mclients.googleapis.com/sj/v2.4/'


class GetNewReleases(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'
    static_url = sj_url + 'explore/tabs'

    @staticmethod
    def dynamic_params(num_items, genre):
        params = {'num-items': num_items}
        if genre is not None:
            params['genre'] = genre
        return params


class GetTopChart(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'
    static_url = sj_url + 'browse/topchart'


class GetTopChartGenres(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'
    static_url = sj_url + 'browse/topchartgenres'


class GetTopChartForGenre(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'

    @staticmethod
    def dynamic_url(genre):
        return sj_url + 'browse/topchartforgenre/' + genre


class GetStationCategories(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'
    static_url = sj_url + 'browse/stationcategories'


class GetStations(McCall):
    static_params = {'alt': 'json'}
    static_method = 'GET'

    @staticmethod
    def dynamic_url(station_id, location_code):
        return sj_url + 'browse/stations/' + station_id

    @staticmethod
    def dynamic_params(station_id, location_code):
        return {'hl': location_code}
