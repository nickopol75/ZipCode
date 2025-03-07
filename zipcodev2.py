import streamlit as st
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialize session state
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

@st.cache_data
def geocode_zip(zip_code):
    geolocator = Nominatim(user_agent="swiss_dealer_finder")
    location = geolocator.geocode(f"{zip_code}, Switzerland")
    return location

def find_closest_zip(input_zip):
    input_location = geocode_zip(input_zip)
    if not input_location:
        return None
    
    closest_zip = None
    min_distance = float('inf')
    
    for zip_code in st.session_state.dealers.keys():
        location = geocode_zip(zip_code)
        if location:
            distance = geodesic((input_location.latitude, input_location.longitude),
                                (location.latitude, location.longitude)).kilometers
            if distance < min_distance:
                min_distance = distance
                closest_zip = zip_code
    
    return closest_zip, min_distance

# Streamlit app
st.title("Swiss Dealer Finder")

# Sidebar for adding and deleting dealers
st.sidebar.header("Manage Dealers")

# Add new dealer
new_zip = st.sidebar.text_input("New Zip Code")
new_dealer = st.sidebar.text_input("New Dealer Name")

if st.sidebar.button("Add Dealer"):
    if new_zip and new_dealer:
        st.session_state.dealers[new_zip] = new_dealer
        st.sidebar.success(f"Added: {new_dealer} at {new_zip}")
    else:
        st.sidebar.error("Please enter both zip code and dealer name")

# Delete dealer
st.sidebar.markdown("---")
delete_zip = st.sidebar.selectbox("Select Zip Code to Delete", options=list(st.session_state.dealers.keys()))

if st.sidebar.button("Delete Dealer"):
    if delete_zip in st.session_state.dealers:
        deleted_dealer = st.session_state.dealers[delete_zip]
        del st.session_state.dealers[delete_zip]
        st.sidebar.success(f"Deleted: {deleted_dealer} at {delete_zip}")
    else:
        st.sidebar.error("Selected zip code not found")

# Main app
input_zip = st.text_input("Enter a Swiss zip code:")

if st.button("Find Closest Dealer"):
    if input_zip:
        with st.spinner("Searching..."):
            result = find_closest_zip(input_zip)
            if result:
                closest_zip, distance = result
                dealer_name = st.session_state.dealers.get(closest_zip, "Unknown Dealer")
                st.success(f"The closest dealer is '{dealer_name}'\nZip code: {closest_zip}\nApproximately {distance:.2f} km away.")
                # Add to search history
                st.session_state.search_history.append(f"Searched: {dealer_name} - CustomerZip: {input_zip}")
            else:
                st.error("Invalid zip code or unable to geocode.")
    else:
        st.warning("Please enter a zip code.")

# Display search history
if st.session_state.search_history:
    st.header("Search History")
    for search in st.session_state.search_history:
        st.text(search)

# Display current dealers
st.header("Current Dealers")
for zip_code, dealer_name in st.session_state.dealers.items():
    st.text(f"{zip_code}: {dealer_name}")
