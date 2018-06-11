import requests
import os, sys
import concurrent.futures
from itertools import repeat

class XimaScraper:
    def __init__(self, album_no):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
        }
        sort_order = '-1'
        album_size = '1000'
        base_url = 'http://www.ximalaya.com/revision/play/'
        url = base_url+'album?albumId={}&pageNum=1&sort={}&pageSize={}'.format(album_no, sort_order, album_size)
        req = requests.get(url, headers=headers)
        self.full_tracks_info = req.json()['data']['tracksAudioPlay']
        self.album_name = self.full_tracks_info[0]['albumName']

    def get_index_trackname_url(self):
        # filename = padded index - trackName, e.g. 001 - trackName
        return [(t['index'], t['trackName'], t['src']) for t in self.full_tracks_info]


# ----------------
# helper functions
# ----------------
def pad_zero(n):
    padded = '000'+n
    return padded[-3:]


def download_from_url(filedir, idx, trackname, url):
    print('requesting ' + trackname)
    filename = pad_zero(str(idx)) + ' - ' + trackname + '.mp3'
    filepath = os.path.join(filedir, filename)
    mp3 = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(mp3.content)
    print('finished ' + trackname)


# download the file then record the downloaded url to a file
def download_and_record(filedir, idx, trackname, url, recordfile):
    download_from_url(filedir, idx, trackname, url)
    with open(recordfile, "a") as f:
        f.write(trackname+'|')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError('Need Album Number')
    album_no = sys.argv[1].strip()
    xima = XimaScraper(album_no)
    filedir = xima.album_name
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    recordfile = os.path.join(filedir, 'record')
    # check existing record file
    try:
        with open(recordfile, "r") as f:
            downloaded_tracks_raw = f.read()
        downloaded_tracks = downloaded_tracks_raw.split('|')
        to_download = [e for e in xima.get_index_trackname_url() if e[1] not in downloaded_tracks]
    except FileNotFoundError:
        to_download = xima.get_index_trackname_url()
    if to_download:
        print('total number of episodes to download: '+str(len(to_download)))
        idxs = [e[0] for e in to_download]
        tracknames = [e[1] for e in to_download]
        urls = [e[2] for e in to_download]
        with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
            executor.map(download_and_record, repeat(filedir), idxs, tracknames, urls, repeat(recordfile))
        print('finished all downloading')
    else:
        print('all episodes are already downloaded')

