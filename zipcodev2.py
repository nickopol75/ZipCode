# Swiss Dealer Finder - Streamlit App with Map Visualization and Two Closest Dealers
import streamlit as st
import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import folium
from streamlit_folium import st_folium

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
    if 'map_data' not in st.session_state:
        st.session_state.map_data = {}
    if 'dealer_result' not in st.session_state:
        st.session_state.dealer_result = None

@st.cache_data(ttl=86400)
def geocode_zip(zip_code):
    try:
        geolocator = Nominatim(user_agent="swiss_dealer_finder_v2")
        return geolocator.geocode(f"{zip_code}, Switzerland", timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

def find_two_closest_dealers(input_zip):
    input_location = geocode_zip(input_zip)
    if not input_location:
        return None, []

    dealer_distances = []
    for zip_code, name in st.session_state.dealers.items():
        location = geocode_zip(zip_code)
        if location:
            try:
                distance = geodesic(
                    (input_location.latitude, input_location.longitude),
                    (location.latitude, location.longitude)
                ).kilometers
                dealer_distances.append((zip_code, name, location, distance))
            except ValueError:
                continue

    dealer_distances.sort(key=lambda x: x[3])  # sort by distance
    return input_location, dealer_distances[:2]

st.set_page_config(page_title="Swiss Dealer Finder", page_icon="🚗", layout="wide")
initialize_session_state()

st.title("🇨🇭 Swiss Dealer Finder")
st.markdown("""
Easily find the two nearest registered car dealers in Switzerland by entering your zip code.
""")

search_col, manage_col = st.columns([2, 1])

with search_col:
    st.header("🔍 Find Dealers")
    with st.form(key="search_form"):
        input_zip = st.text_input("Enter a Swiss zip code:", max_chars=4, placeholder="e.g., 8001")
        submit_button = st.form_submit_button("Find Closest Dealers")

    if submit_button:
        if input_zip and input_zip.isdigit() and len(input_zip) == 4:
            with st.spinner("Finding closest dealers..."):
                time.sleep(0.5)
                input_location, top_two = find_two_closest_dealers(input_zip)
                if top_two:
                    st.session_state.search_history.append({
                        'input_zip': input_zip,
                        'dealer': top_two[0][1],
                        'dealer_zip': top_two[0][0],
                        'distance': top_two[0][3],
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    })

                    result_msg = (
                        f"**Closest Dealer:**\n"
                        f"Name: {top_two[0][1]}\nZip: {top_two[0][0]}\nDistance: {top_two[0][3]:.2f} km\n\n"
                        f"**Second Closest Dealer:**\n"
                        f"Name: {top_two[1][1]}\nZip: {top_two[1][0]}\nDistance: {top_two[1][3]:.2f} km"
                    )
                    st.session_state.dealer_result = result_msg
                    st.session_state.map_data = {
                        'input_zip': input_zip,
                        'input_location': (input_location.latitude, input_location.longitude),
                        'dealers': [
                            {
                                'name': top_two[0][1], 'zip': top_two[0][0],
                                'latlon': (top_two[0][2].latitude, top_two[0][2].longitude),
                                'distance': top_two[0][3], 'rank': 'Closest'
                            },
                            {
                                'name': top_two[1][1], 'zip': top_two[1][0],
                                'latlon': (top_two[1][2].latitude, top_two[1][2].longitude),
                                'distance': top_two[1][3], 'rank': 'Second Closest'
                            }
                        ]
                    }
                else:
                    st.error("No dealers found for the given zip code.")
        else:
            st.warning("Please enter a valid 4-digit Swiss zip code.")

    if st.session_state.dealer_result:
        st.success(st.session_state.dealer_result)

if st.session_state.map_data:
    data = st.session_state.map_data
    input_lat, input_lon = data['input_location']
    m = folium.Map(location=[input_lat, input_lon], zoom_start=11)
    folium.Marker(
        [input_lat, input_lon],
        popup=f"Input Zip: {data['input_zip']}",
        tooltip="You are here",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)

    for dealer in data['dealers']:
        lat, lon = dealer['latlon']
        folium.Marker(
            [lat, lon],
            popup=f"{dealer['rank']} Dealer: {dealer['name']} ({dealer['zip']})\n{dealer['distance']:.2f} km",
            tooltip=dealer['rank'],
            icon=folium.Icon(color="green" if dealer['rank'] == 'Closest' else "orange", icon="car")
        ).add_to(m)
        folium.PolyLine(
            [(input_lat, input_lon), (lat, lon)],
            color="red" if dealer['rank'] == 'Closest' else "orange",
            weight=2.5,
            opacity=1
        ).add_to(m)

    st.markdown("### 🗺️ Dealer Map")
    st_folium(m, width=700)

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

st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Folium, and Geopy | Data: Swiss Zip Codes")
