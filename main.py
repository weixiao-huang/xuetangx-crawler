from crawler import download_all, download_srt_file, download_improve

url = 'http://www.xuetangx.com/courses/course-v1:TsinghuaX+20220332X+2018_T2/courseware/a1039c2138944208a18a83d3c14dd799/f33a4efe2738403ba73cccd510fafb38/'

if __name__ == '__main__':
    download_improve(url)
    # download_srt_file(url)
