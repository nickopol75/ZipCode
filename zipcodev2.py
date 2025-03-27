import streamlit as st
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pandas as pd

# Initialize session state with default dealers
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

# Enhanced caching with TTL and error handling
@st.cache_data(ttl=86400)  # Cache for 24 hours
def geocode_zip(zip_code):
    try:
        geolocator = Nominatim(user_agent="swiss_dealer_finder_v2")
        location = geolocator.geocode(f"{zip_code}, Switzerland", timeout=10)
        return location
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

def find_closest_dealer(input_zip):
    input_location = geocode_zip(input_zip)
    if not input_location:
        return None, None
    
    closest_zip = None
    min_distance = float('inf')
    
    for zip_code in st.session_state.dealers.keys():
        location = geocode_zip(zip_code)
        if location:
            try:
                distance = geodesic(
                    (input_location.latitude, input_location.longitude),
                    (location.latitude, location.longitude)
                ).kilometers
                if distance < min_distance:
                    min_distance = distance
                    closest_zip = zip_code
            except ValueError:
                continue
    
    return closest_zip, min_distance

# Streamlit app configuration
st.set_page_config(page_title="Swiss Dealer Finder", layout="wide")
initialize_session_state()

# Main title and description
st.title("🇨🇭 Swiss Dealer Finder")
st.markdown("Find the nearest car dealer based on Swiss zip codes.")

# Two-column layout
col1, col2 = st.columns([2, 1])

# Main search functionality
with col1:
    st.subheader("Find a Dealer")
    with st.form(key='search_form'):
        input_zip = st.text_input("Enter a Swiss zip code (4 digits):", max_chars=4)
        submit_button = st.form_submit_button(label="Find Closest Dealer")
    
    if submit_button:
        if input_zip and input_zip.isdigit() and len(input_zip) == 4:
            with st.spinner("Locating nearest dealer..."):
                time.sleep(0.5)  # Small delay for better UX
                closest_zip, distance = find_closest_dealer(input_zip)
                if closest_zip:
                    dealer_name = st.session_state.dealers[closest_zip]
                    st.success(
                        f"**Closest Dealer Found**\n\n"
                        f"Name: {dealer_name}\n"
                        f"Zip: {closest_zip}\n"
                        f"Distance: {distance:.2f} km"
                    )
                    st.session_state.search_history.append({
                        'input_zip': input_zip,
                        'dealer': dealer_name,
                        'dealer_zip': closest_zip,
                        'distance': distance,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                else:
                    st.error("Unable to find a dealer for this zip code.")
        else:
            st.warning("Please enter a valid 4-digit Swiss zip code.")

# Sidebar for dealer management
with col2:
    st.subheader("Manage Dealers")
    with st.expander("Add New Dealer", expanded=False):
        new_zip = st.text_input("Zip Code", key="new_zip", max_chars=4)
        new_dealer = st.text_input("Dealer Name", key="new_dealer")
        if st.button("Add Dealer"):
            if new_zip and new_dealer and new_zip.isdigit() and len(new_zip) == 4:
                if new_zip not in st.session_state.dealers:
                    st.session_state.dealers[new_zip] = new_dealer
                    st.success(f"Added: {new_dealer} ({new_zip})")
                else:
                    st.warning("Zip code already exists!")
            else:
                st.error("Enter a valid 4-digit zip code and dealer name")
    
    with st.expander("Remove Dealer", expanded=False):
        delete_zip = st.selectbox("Select Dealer to Remove", 
                                options=list(st.session_state.dealers.keys()))
        if st.button("Remove Dealer"):
            dealer_name = st.session_state.dealers.pop(delete_zip)
            st.success(f"Removed: {dealer_name} ({delete_zip})")

# Display dealers and search history using tabs
tab1, tab2 = st.tabs(["Current Dealers", "Search History"])

with tab1:
    df_dealers = pd.DataFrame(
        list(st.session_state.dealers.items()),
        columns=['Zip Code', 'Dealer Name']
    )
    st.dataframe(df_dealers, use_container_width=True)

with tab2:
    if st.session_state.search_history:
        df_history = pd.DataFrame(st.session_state.search_history)
        st.dataframe(df_history[['timestamp', 'input_zip', 'dealer', 'dealer_zip', 'distance']],
                    use_container_width=True)
    else:
        st.info("No search history yet.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | Data: Swiss Zip Codes")
