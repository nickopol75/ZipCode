# Swiss Dealer Finder - Professional Streamlit Interface
import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Initialize dealer data and search history in session state
def initialize_session_state():
    if 'dealers' not in st.session_state:
        st.session_state.dealers = {
            "3076": "Bächelmatt Garage Worb",
            "8106": "Garage R. Wallishauser AG",
            "3613": "Autohaus Thun-Nord AG",
            "7205": "Garage O. Stock AG",
            "4503": "Gysin + Gerspacher AG",
            "9500": "alphaCARS.CH AG – Wil",
            "5432": "Garage Matter AG",
            "9014": "alphaCARS.CH AG – Oberuzwil",
            "9242": "alphaCARS.CH AG – St. Gallen",
            "6467": "Brand Automobile AG",
            "4950": "Garage Rupli"
        }
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

# Cache geolocation results
@st.cache_data(ttl=86400)
def geocode_zip(zip_code):
    try:
        geolocator = Nominatim(user_agent="swiss_dealer_finder_v2")
        return geolocator.geocode(f"{zip_code}, Switzerland", timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

# Find closest dealer by zip code
def find_closest_dealer(input_zip):
    input_location = geocode_zip(input_zip)
    if not input_location:
        return None, None

    closest_zip = None
    min_distance = float('inf')

    for zip_code in st.session_state.dealers:
        location = geocode_zip(zip_code)
        if location:
            try:
                distance = geodesic(
                    (input_location.latitude, input_location.longitude),
                    (location.latitude, location.longitude)
                ).kilometers
                if distance < min_distance:
                    closest_zip = zip_code
                    min_distance = distance
            except ValueError:
                continue

    return closest_zip, min_distance

# App configuration
st.set_page_config(page_title="Swiss Dealer Finder", page_icon="🚗", layout="wide")
initialize_session_state()

# Header
st.title("🇨🇭 Swiss Dealer Finder")
st.markdown("""
Easily find the nearest registered car dealer in Switzerland by entering your zip code.
""")

# Layout
search_col, manage_col = st.columns([2, 1])

# Search Section
with search_col:
    st.header("🔍 Find a Dealer")
    with st.form(key="search_form"):
        input_zip = st.text_input("Enter a Swiss zip code:", max_chars=4, placeholder="e.g., 8001")
        submit_button = st.form_submit_button("Find Closest Dealer")

    if submit_button:
        if input_zip and input_zip.isdigit() and len(input_zip) == 4:
            with st.spinner("Locating nearest dealer..."):
                time.sleep(0.5)
                closest_zip, distance = find_closest_dealer(input_zip)
                if closest_zip:
                    dealer_name = st.session_state.dealers[closest_zip]
                    st.success(f"**{dealer_name}**\nZip: {closest_zip} | Distance: {distance:.2f} km")
                    st.session_state.search_history.append({
                        'input_zip': input_zip,
                        'dealer': dealer_name,
                        'dealer_zip': closest_zip,
                        'distance': distance,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    st.error("No dealer found for the given zip code.")
        else:
            st.warning("Please enter a valid 4-digit Swiss zip code.")

# Management Section
with manage_col:
    st.header("⚙️ Manage Dealers")
    with st.expander("➕ Add Dealer"):
        new_zip = st.text_input("Zip Code", key="new_zip", max_chars=4)
        new_dealer = st.text_input("Dealer Name", key="new_dealer")
        if st.button("Add Dealer"):
            if new_zip and new_dealer and new_zip.isdigit() and len(new_zip) == 4:
                if new_zip not in st.session_state.dealers:
                    st.session_state.dealers[new_zip] = new_dealer
                    st.success(f"Added {new_dealer} ({new_zip})")
                else:
                    st.warning("Zip code already exists.")
            else:
                st.error("Please provide a valid zip code and dealer name.")

    with st.expander("🗑️ Remove Dealer"):
        if st.session_state.dealers:
            delete_zip = st.selectbox("Select Dealer to Remove", list(st.session_state.dealers.keys()))
            if st.button("Remove Dealer"):
                dealer_name = st.session_state.dealers.pop(delete_zip)
                st.success(f"Removed {dealer_name} ({delete_zip})")

# Tabs for data display
tab1, tab2 = st.tabs(["📍 Current Dealers", "🕘 Search History"])

with tab1:
    st.dataframe(pd.DataFrame(
        st.session_state.dealers.items(),
        columns=["Zip Code", "Dealer Name"]
    ), use_container_width=True)

with tab2:
    if st.session_state.search_history:
        df_history = pd.DataFrame(st.session_state.search_history)
        st.dataframe(df_history[["timestamp", "input_zip", "dealer", "dealer_zip", "distance"]],
                     use_container_width=True)
    else:
        st.info("No search history yet.")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit | Powered by Geopy | Data: Swiss Zip Codes")
