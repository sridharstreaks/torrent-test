import streamlit as st
from stqdm import stqdm
import libtorrent as lt
import time
import os

# Set up a directory for temporary storage
temp_dir = "temp_video"
os.makedirs(temp_dir, exist_ok=True)

# Initialize session state for libtorrent session and handle
if "torrent_session" not in st.session_state:
    st.session_state.torrent_session = lt.session()
    st.session_state.torrent_handle = None

# Function: get_domian
def domain_finder(previous_domain='.ru'):
    base_url="https://www.1tamilmv"
    response = requests.get(base_url+previous_domain)
    if response.status_code==200:
        tree = html.fromstring(response.content)
        current_domain=tree.xpath('//*[contains(text(),".") and @class]/text()')[0]
    current_url=base_url+current_domain
    return current_url  #redirection pending

# Function: movie_search
def movie_search(query,previous_domain='.ru'):
    dicto={}
    discard_words=['gdrive','Trailer']
    query=query.replace(" ","%20").lower()
    url=f"{domain_finder(previous_domain)}/index.php?/search/&q={query}&quick=1&search_and_or=and&search_in=titles&sortby=relevancy"
    response = requests.get(url)
    if response.status_code==200:
        tree = html.fromstring(response.content)
        range_inc=5
        for i in range(0,range_inc):
            try:
                if not any(dword.lower() in tree.xpath('//li[@data-role="activityItem"]//h2//a//text()')[i].lower() for dword in discard_words):
                    dicto[tree.xpath('//li[@data-role="activityItem"]//h2//a//text()')[i]] = tree.xpath('//li[@data-role="activityItem"]//h2//a//@href')[i]
                else:
                    range_inc+=1
            except IndexError:
                    break
    return dicto

# Function: movie_quality
def movie_quality(link):
    dicto={}
    response = requests.get(link)
    if response.status_code==200:
        tree = html.fromstring(response.content)
    for i in range(0,int(tree.xpath('count(//a[@class="skyblue-button"]/@href)'))):
        dicto[tree.xpath('//a[@class="skyblue-button"]//preceding-sibling::strong[2]/text()')[i]]=tree.xpath('//a[@class="skyblue-button"]/@href')[i]
    return dicto

# Function: movie_torrent
def start_download(magnet_link, save_path):
    """Start or resume downloading a torrent."""
    ses = st.session_state.torrent_session
    ses.apply_settings({'listen_interfaces': '0.0.0.0:6881,[::]:6881'})

    params = lt.add_torrent_params()
    params.save_path = save_path
    params.storage_mode = lt.storage_mode_t(2)
    params.url = magnet_link

    handle = ses.add_torrent(params)
    st.session_state.torrent_handle = handle

    st.write("Downloading Metadata...")
    while not handle.status().has_metadata:
        time.sleep(1)
    st.write("Metadata Imported, Starting Download...")

# Monitor download progress with stqdm

def monitor_download():
    """Monitor download progress."""
    handle = st.session_state.torrent_handle
    if handle is None:
        st.warning("No active download session. Start a new download.")
        return

    st.write("Download Progress:")
    progress_bar = stqdm(range(100))
    while handle.status().state != lt.torrent_status.seeding:
        s = handle.status()
        progress = int(s.progress * 100)
        for _ in progress_bar[:progress]:
            pass
        stqdm.write(f"{progress}% complete")
        time.sleep(5)

    st.success("Download Complete!")

# Streamlit UI
st.title("Torrent Video Downloader")

# Step 1: Movie Search
query = st.text_input("Enter movie name:")
if query.strip():
    if st.button("Search"):
        search_results = movie_search(query)
        selected_movie = st.pills("Select a movie:", list(search_results.keys()))
        if st.button("Confirm Selection"):
            st.session_state.selected_movie_link = search_results[selected_movie]

# Step 2: Movie Quality
if "selected_movie_link" in st.session_state:
    quality_results = movie_quality(st.session_state.selected_movie_link)
    selected_quality = st.pills("Select quality:", list(quality_results.keys()))
    if st.button("Confirm Quality"):
        st.session_state.selected_quality_link = quality_results[selected_quality]

# Step 3: Torrent Download
if "selected_quality_link" in st.session_state:
    if st.button("Start Download"):
        start_download(st.session_state.selected_quality_link, temp_dir)

    if st.button("Monitor Progress"):
        monitor_download()

    # Optional cleanup button to remove temporary files
    if st.button("Clear Temporary Files"):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        st.success("Temporary files cleared.")
