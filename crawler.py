import requests
from bs4 import BeautifulSoup
import re
import json
import os
from auth import headers, cookies

server_addr = 'http://www.xuetangx.com'
default_path = '/courses/course-v1:TsinghuaX+30240243X+sp/courseware/02ccdcfc806147e1a180205857acee3a/'

default_url = server_addr + default_path


def get_from_url(url=default_url):
    return requests.get(url, headers=headers, cookies=cookies).text


def parse_section_list(url):
    soup = BeautifulSoup(get_from_url(url), 'lxml')
    x = soup.find_all('li')
    section_list = []
    chapter_id = 0
    for i in range(len(x)):
        li = x[i]
        try:
            a = li.contents[1]
            p = a.contents[1]
            if len(p.attrs) != 0:
                continue
            title = p.contents[0]
            href = a.attrs['href']
        except IndexError:
            continue
        if i > 0:
            li_prev = x[i - 1]
            if li.parent != li_prev.parent:
                chapter_id += 1
        section_list.append({
            'title': title,
            'url': href,
            'chapter_id': chapter_id
        })
    return section_list


video_addr_prefix = 'http://www.xuetangx.com/videoid2source/'


def parse_video_obj(url):
    soup = BeautifulSoup(get_from_url(url), 'lxml')
    a = soup.find_all(id=re.compile('seq_contents_\d+'))
    regx = r'data-ccsource=\'[a-zA-Z0-9]*\''
    text = re.findall(regx, a.decode())[0]
    video_id = text.split('\'')[1]
    regx = r'data-transcript-translation-url=\".*\"'
    text = re.findall(regx, a.decode())[0]
    srt_id = text.split('\"')[1]
    url = video_addr_prefix + video_id
    srt_url = server_addr + srt_id + '/zh'
    return json.loads(requests.get(url).text)


def parse_videos(url):
    soup = BeautifulSoup(get_from_url(url), 'lxml')
    seq_contents = soup.find_all(id=re.compile('seq_contents_\d+'))

    v_regx = r'data-ccsource=\'[a-zA-Z0-9]*\''
    s_regx = r'data-transcript-translation-url=\".*\"'

    videos = []
    for x in seq_contents:
        x = x.decode()
        v_list = re.findall(v_regx, x)
        if len(v_list) > 0:
            v_url = video_addr_prefix + v_list[0].split('\'')[1]
            try:
                video = json.loads(requests.get(v_url).text)
            except Exception as e:
                print('no video in this block, error: %s' % e)
                continue
            srt = None
            s_list = re.findall(s_regx, x)
            if len(s_list) > 0:
                try:
                    s_url = server_addr + s_list[0].split('\"')[1] + '/zh'
                    srt = json.loads(get_from_url(s_url))
                except Exception as e:
                    print('no srt in this block, error: %s' % e)
            videos.append({
                'video': video,
                'srt': srt
            })
    return videos


def parse_srt(url):
    try:
        soup = BeautifulSoup(get_from_url(url), 'lxml')
        a = soup.find(id='seq_contents_0')
        regx = r'data-transcript-translation-url=\".*\"'
        text = re.findall(regx, a.decode())[0]
        srt_id = text.split('\"')[1]
        srt_url = server_addr + srt_id + '/zh'
        data = json.loads(get_from_url(srt_url))
        return data
    except Exception as e:
        print('error in parse srt \"%s\", error is: %s' % (url, e))
        return None


def write_srt_file(srt_obj, fn='demo.srt'):
    text = srt_obj['text']
    start = srt_obj['start']
    end = srt_obj['end']
    with open(fn, 'w') as f:
        for i in range(len(text)):
            start_h = start[i] // 3600000
            start_m = start[i] // 60000
            start_s = start[i] % 60000 // 1000
            start_ms = start[i] % 60000 % 1000
            end_h = end[i] // 3600000
            end_m = end[i] // 60000
            end_s = end[i] % 60000 // 1000
            end_ms = end[i] % 60000 % 1000
            start_str = '%02d:%02d:%02d,%03d' % (start_h, start_m, start_s, start_ms)
            end_str = '%02d:%02d:%02d,%03d' % (end_h, end_m, end_s, end_ms)
            f.write(str(i + 1) + '\n')
            f.write('%s --> %s\n' % (start_str, end_str))
            f.write(text[i] + '\n\n')
    return fn


def get_video_url(url, quality=2):
    video_obj = parse_video_obj(url)
    if quality == 2:
        return video_obj['sources']['quality20'][0]
    else:
        return video_obj['sources']['quality10'][0]


def download_file(url, fn=None):
    if not fn:
        fn = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(fn, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian
    return fn


def download_all(url):
    print('parse section list start...')
    sections = parse_section_list(url)
    print('parse section list success...')
    for section in sections:
        fn = section['title'].strip().replace('/', ' ') + '.mp4'
        print('downloading %s ...' % fn)
        if os.path.exists(fn):
            continue
        try:
            video_url = get_video_url(server_addr + section['url'])
            download_file(video_url, fn)
            print('downloading %s success' % fn)
        except IndexError:
            print('section %s do not have video' % fn)
            pass


def download_srt_file(url):
    print('parse section list start...')
    sections = parse_section_list(url)
    print('parse section list success...')
    for section in sections:
        title = section['title'].strip().replace('/', ' ')
        fn = title + '.srt'
        print('downloading %s ...' % fn)
        if os.path.exists(fn):
            continue
        try:
            srt_obj = parse_srt(server_addr + section['url'])
            if not srt_obj:
                continue
            write_srt_file(srt_obj, fn)
            print('downloading %s success' % fn)
        except IndexError:
            print('section %s do not have srt file' % fn)
            pass
        except Exception as e:
            print('other error in section %s, error is: %s' % e)


def download_improve(url):
    print('parse section list start...')
    sections = parse_section_list(url)
    print('parse section list success...')
    chapter_id = 0
    section_id = 0
    for section in sections:
        if section['chapter_id'] != chapter_id:
            chapter_id = section['chapter_id']
            section_id = 1
        else:
            section_id += 1
        dir = '%02d' % chapter_id
        if not os.path.exists(dir):
            os.mkdir(dir)
        title = section['title'].strip().replace('/', ' ')
        title = '%d.%d-%s' % (chapter_id, section_id, title)

        print('---------- parsing videos: %s ... ----------' % title)
        videos = parse_videos(server_addr + section['url'])

        i = 1
        for video in videos:
            # download video
            name = '%s-%02d' % (title, i)
            if len(videos) == 1:
                name = title

            if os.path.exists(os.path.join(dir, name + '.mp4')):
                print('video have already been downloaded.')
                continue

            print('downloading %s.mp4...' % name)
            try:
                video_url = video['video']['sources']['quality20'][0]
                download_file(video_url, os.path.join(dir, name + '.mp4'))
            except IndexError:
                print('section %s do not have video' % name)
                continue

            i += 1
            if os.path.exists(os.path.join(dir, name + '.srt')):
                print('srt file have already been downloaded.')
                continue
            # write srt
            try:
                srt_obj = video['srt']
                if not srt_obj:
                    continue
                print('writing %s.srt...' % name)
                write_srt_file(srt_obj, os.path.join(dir, name + '.srt'))
            except IndexError:
                print('section %s do not have srt file' % name)
                continue
            except Exception as e:
                print('other error in section %s, error is: %s' % e)
                continue
